# -*- coding: utf-8 -*-

"""
This module provides the framework for formulas. All formulas should inherit
from the Formula class in this module. Formula sources must include a
formula importer, or can subclass one of the formula importers here.
"""

from carousel.core import Registry, CommonBase, UREG, logging
import json
import imp
import importlib
import os
import sys
import numexpr as ne
import inspect
from uncertainty_wrapper import unc_wrapper_args

LOGGER = logging.getLogger(__name__)


class FormulaRegistry(Registry):
    """
    A registry for formulas.
    """
    _meta_names = ['islinear', 'args', 'units', 'isconstant']

    def __init__(self):
        super(FormulaRegistry, self).__init__()
        #: ``True`` if formula is linear, ``False`` if non-linear.
        self.islinear = {}
        #: positional arguments
        self.args = {}
        #: expected units of returns and arguments as pair of tuples
        self.units = {}
        #: constant arguments that are not included in covariance calculation
        self.isconstant = {}

    def register(self, new_formulas, *args, **kwargs):
        kwargs.update(zip(self._meta_names, args))
        # call super method, meta must be passed as kwargs!
        super(FormulaRegistry, self).register(new_formulas, **kwargs)


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
    """
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
            # expand ~, environmental variables and make it absolute path
            if not os.path.isabs(path):
                path = os.path.expanduser(os.path.expandvars(path))
                path = os.path.abspath(path)
            # paths must be a list
            paths = [path]
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
            formulas = {f: getattr(mod, f) for f in dir(mod) if f[:2] == 'f_'}
        return formulas


# methods for auto detecting functions in module
# do it using types.FunctionType
#             import types
#             f = {f: getattr(mod, f)
#                  for f in mod_attr
#                  if isinstance(getattr(mod, f), types.FunctionType)}
# do it using inspect.isfunction()
#             import inspect
#             f = {f: getattr(mod, f)
#                  for f in mod_attr if inspect.isfunction(getattr(mod, f))}


class NumericalExpressionImporter(FormulaImporter):
    """
    Import formulas from numerical expressions using Python Numexpr.
    """
    def import_formulas(self):
        formulas = {}  # an empty list of formulas
        formula_param = self.parameters.get('formulas')  # formulas key
        for f, p in formula_param.iteritems():
            formulas[f] = lambda *args: ne.evaluate(
                p['expression'], {k: a for k, a in zip(p['args'], args)}, {}
            )


class FormulaBase(CommonBase):
    """
    Metaclass for formulas.
    """
    _path_attr = 'formulas_path'
    _file_attr = 'formulas_file'

    def __new__(mcs, name, bases, attr):
        # use only with Formula subclasses
        if not CommonBase.get_parents(bases, FormulaBase):
            return super(FormulaBase, mcs).__new__(mcs, name, bases, attr)
        # set param file full path if formulas path and file specified or
        # try to set parameters from class attributes except private/magic
        attr = mcs.set_param_file_or_parameters(attr)
        return super(FormulaBase, mcs).__new__(mcs, name, bases, attr)


class Formula(object):
    """
    A class for formulas.

    Specify ``formula_importer`` which must subclass :class:`FormulaImporter`
    to import formula source files as class. If no ``formula_importer`` is
    specified, the default is
    :class:`~carousel.core.formulas.PyModuleImporter`.

    Specify ``formula_path`` and ``formula_file`` that contains formulas in
    string form or parameters used to import the formula source file.

    This is the required interface for all source files containing formulas
    used in Carousel.
    """
    __metaclass__ = FormulaBase
    #: formula importer class, default is ``PyModuleImporter``
    formula_importer = PyModuleImporter  # can be overloaded in superclass

    def __init__(self):
        if hasattr(self, 'param_file'):
            # read and load JSON parameter map file as "parameters"
            with open(self.param_file, 'r') as fp:
                #: dictionary of parameters for reading formula source file
                self.parameters = json.load(fp)
        else:
            #: parameter file
            self.param_file = None
        # check for path listed in param file
        if 'path' in self.parameters and self.parameters.get('path') is None:
            proxy_file = self.param_file if self.param_file else __file__
            # use the same path as the param file or this file if no param file
            self.parameters['path'] = os.path.dirname(proxy_file)
        #: formulas loaded by the importer using specified parameters
        self.formulas = self.formula_importer(self.parameters).import_formulas()
        #: linearity determined by each data source?
        self.islinear = {}
        #: positional arguments
        self.args = {}
        #: expected units of returns and arguments as pair of tuples
        self.units = {}
        #: constant arguments that are not included in covariance calculation
        self.isconstant = {}
        formula_param = self.parameters.get('formulas')  # formulas key
        try:
            # formula dictionary
            for k, v in formula_param.iteritems():
                if not v:
                    # skip formula if attributes are null or empty
                    continue
                # get islinear formula attribute
                self.islinear[k] = v.get('islinear', True)
                # get positional arguments
                self.args[k] = v.get('args')
                if self.args[k] is None:
                    # use inspect if args not specified
                    self.args[k] = inspect.getargspec(self.formulas[k]).args
                # get constant arguments to exclude from covariance
                self.isconstant[k] = v.get('isconstant')
                if self.isconstant[k] is not None:
                    argn = [n for n, a in enumerate(self.args[k]) if a not in
                            self.isconstant[k]]
                    LOGGER.debug('%s arg nums: %r', k, argn)
                    self.formulas[k] = unc_wrapper_args(*argn)(self.formulas[k])
                # get units of returns and arguments
                self.units[k] = v.get('units')
                if self.units[k] is not None:
                    # append units for covariance and Jacobian if all args
                    # constant and more than one return output
                    if self.isconstant[k] is not None:
                        if isinstance(self.units[k][0], basestring):
                            self.units[k][0] = [self.units[k][0]]
                        try:
                            self.units[k][0] += [None, None]
                        except TypeError:
                            self.units[k][0] += (None, None)
                    # wrap function with Pint's unit wrapper
                    self.formulas[k] = UREG.wraps(*self.units[k])(
                        self.formulas[k]
                    )
        except TypeError:
            # sequence of formulas, don't propagate uncertainty or units
            for f in self.formulas:
                self.islinear[f] = True
                self.args[f] = inspect.getargspec(self.formulas[f]).args

    def __getitem__(self, item):
        return self.formulas[item]
