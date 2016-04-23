# -*- coding: utf-8 -*-

"""
This module provides the framework for formulas. All formulas should inherit
from the Formula class in this module. Formula sources must include a
formula importer, or can subclass one of the formula importers here.
"""

import json
import imp
import importlib
import os
import sys
import numexpr as ne
from circus.core import Registry


class FormulaRegistry(Registry):
    """
    A registry for formulas.
    """
    def __init__(self):
        super(FormulaRegistry, self).__init__()
        #: ``True`` if formula is linear, ``False`` if non-linear.
        self.islinear = {}

    def register(self, new_formulas, *args):
        islinear = args[0]
        # call super method, meta must be passed as kwargs!
        super(FormulaRegistry, self).register(new_formulas, islinear=islinear)


class Formula(object):
    """
    A class for formulas.

    :param formula_importer: A class used to import formula source files.
    :type formula_importer: :class:`FormulaImporter`
    :param param_file: Name of file that contains formulas in string form or
        parameters used to import the formula source file.
    :type param_file: str

    This is the required interface for all source files containing formulas
    used in Circus.
    """
    def __init__(self, formula_importer, param_file):
        # read and load JSON parameter map file as "parameters"
        with open(param_file, 'r') as fp:
            #: dictionary of parameters for reading formula source file
            self.parameters = json.load(fp)
        path = self.parameters.get('path')  # path listed in json file
        if not path:
            # use the same path as the json file
            path, _ = os.path.split(param_file)
            self.parameters['path'] = path
        # create the formula importer object specified using parameters
        _formula_importer = formula_importer(self.parameters)
        #: formulas loaded by the importer
        self.formulas = _formula_importer.import_formulas()
        #: linearity determined by each data source?
        self.islinear = {}
        # linearity
        formula_param = self.parameters.get('formulas')  # formulas key
        try:
            # iterate through formulas
            for k, v in formula_param.iteritems():
                self.islinear[k] = v.get('islinear', True)
        except:
            for f in self.formulas:
                self.islinear[f] = True

    def __getitem__(self, item):
        return self.formulas[item]


# TODO: refactor with meta classes like other layers


class FormulaImporter(object):
    """
    A class that imports formulas.

    :param parameters: Parameters used to import formulas.
    :type parameters: dict
    """
    def __init__(self, parameters):
        #: parameters to be read by reader
        self.parameters = parameters

    def import_formulas(self):
        """
        This method must be implemented by each formula importer.

        :returns: Formulas.
        :rtype: dict
        :raises: :exc:`~exceptions.NotImplementedError`
        """
        raise NotImplementedError(' '.join(['Function "import_formulas" is',
                                            'not implemented.']))


class PyModuleImporter(FormulaImporter):
    """
    Import formulas from a Python module.

    :param parameters: Parameters used to import formulas.
    :type parameters: dict
    """
    def __init__(self, parameters):
        super(PyModuleImporter, self).__init__(parameters)

    def import_formulas(self):
        """
        Import formulas specified in :attr:`parameters`.

        :returns: formulas
        :rtype: dict
        """
        # TODO: unit tests!
        # TODO: move this to somewhere else and call it "importy", maybe
        # core.__init__.py since a lot of modules might use it.
        module = self.parameters['module']  # module read from parameters
        package = self.parameters.get('package')  # package read from params
        name = package + module if package else module  # concat pkg + name
        path = self.parameters.get('path')  # path read from parameters
        # expand ~, environmental variables and make it absolute path
        if not os.path.isabs(path):
            path = os.path.expanduser(os.path.expandvars(path))
            path = os.path.abspath(path)
        # paths must be a list
        paths = [path]
        # import module using module & package keys in parameter file
        # SEE ALSO: http://docs.python.org/2/library/imp.html#examples
        if not path:
            try:
                # fast path: see if module was already imported
                mod = sys.modules[name]
            except KeyError:
                # import module specified in parameters
                mod = importlib.import_module(module, package)
        else:
            # import module and path from parameters file.
            # FYI: don't combine statements in try blocks, otherwise you won't
            # know what raised the exception!
            # FYI: imp.load_source() is more suited to loading a module as
            # something other than its filename into sys.modules dictionary.
            # Find the module by name and path, return open file, pathname, &c.
            fp, filename, description = imp.find_module(name, paths)
            # try to load the module (reloads if already loaded)
            try:
                mod = imp.load_module(name, fp, filename, description)
            finally:
                if fp:
                    fp.close()
        formulas = {}  # an empty list of formulas
        formula_param = self.parameters.get('formulas')  # formulas key
        # FYI: iterating over dictionary is equivalent to iterkeys()
        if isinstance(formula_param, (list, tuple, dict)):
            # iterate through formulas
            for f in formula_param:
                formulas[f] = getattr(mod, f)
        elif isinstance(formula_param, basestring):
            # only one formula
            # FYI: use basestring to test for str and unicode
            # SEE: http://docs.python.org/2/library/functions.html#basestring
            formulas[formula_param] = getattr(mod, formula_param)
        else:
            # autodetect formulas assuming first letter is f
            f = {f: getattr(mod, f) for f in dir(mod) if f[:2] == 'f_'}
# do it using types.FunctionType
#             import types
#             f = {f: getattr(mod, f)
#                  for f in mod_attr
#                  if isinstance(getattr(mod, f), types.FunctionType)}
# do it using inspect.isfunction()
#             import inspect
#             f = {f: getattr(mod, f)
#                  for f in mod_attr if inspect.isfunction(getattr(mod, f))}
        return formulas


class NumericalExpressionImporter(FormulaImporter):
    """
    Import formulas from numerical expressions using Python Numexpr.
    """
    def __init__(self, parameters):
        super(PyModuleImporter, self).__init__(parameters)

    def import_formulas(self):
        formulas = {}  # an empty list of formulas
        formula_param = self.parameters.get('formulas')  # formulas key
        for f, p in formula_param.iteritems():
            formulas[f] = lambda *args: ne.evaluate(
                p['expression'], {k: a for k, a in zip(p['args'], args)}, {}
            )
