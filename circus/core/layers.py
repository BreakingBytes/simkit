# -*- coding: utf-8 -*-
"""
This is the Layers module. There are five layers in a Circus model:

* Data
* Formulas
* Calculations
* Outputs
* Simluation

Layers are used to assemble the model. For example, the data layer assembles
all of the :ref:`data-sources`, calling the :ref:`data-readers` and putting all
of the data (and meta) into the
:class:`~circus.core.data_sources.DataRegistry`.

In general all model layers have add, open and
:meth:`~circus.core.layers.Layer.load` methods. The add method adds
a particular format such as a
:class:`~circus.core.data_sources.DataSource`. The open method gets
data from a file in the format that was added. The
:meth:`~circus.core.layers.Layer.load` method loads the layer into
the model. The :meth:`~circus.core.layers.Layer.load` method must
be implemented in each subclass of
:class:`~circus.core.layers.Layer` or
:exc:`~exceptions.NotImplementedError` is raised.
"""

import importlib
import os

from circus.core import _DATA, Registry, _SIMULATIONS
from data_sources import DataRegistry
from formulas import FormulaRegistry
from circus.core.calculation import CalcRegistry
from outputs import OutputRegistry


class Layer(object):
    """
    A layer in the model.

    :param layer_data: Dictionary of model data specific to this layer.
    :type layer_data: dict
    """
    def __init__(self, layer_data=None):
        #: dictionary of model data specific to this layer
        self.layer = layer_data

    def load(self):
        """
        Load the layer from the model data. This method must be implemented by
        each layer.

        :raises: :exc:`~exceptions.NotImplementedError`
        """
        raise NotImplementedError


class Data(Layer):
    """
    The Data layer of the model.

    :param data: Dictionary of model data specific to the data layer.
    :type data: dict

    The :attr:`~Layer.layer` attribute is a dictionary of data sources names
    as keys of dictionaries for each data source with the module and optionally
    the package containing the module, the filename, which can be ``None``,
    containing specific data for the data source and an optional path to the
    data file. If the path is ``None``, then the default path for data internal
    to Circus is used. External data files should specify the path.
    """
    def __init__(self, data=None):
        super(Data, self).__init__(data)
        #: dictionary of data sources added to the Data layer
        self.data_sources = {}
        #: data source objects
        self.data_obj = {}
        #: data
        self.data = DataRegistry()
        # layers are initialized by the model

    def add(self, data_source, module, package=None):
        """
        Add data_source to model. Tries to import module, then looks for data
        source class definition.

        :param data_source: Name of data source to add.
        :type data_source: str
        :param module: Module in which data source resides. Can be absolute or
            relative. See :func:`importlib.import_module`
        :type module: str
        :param package: Optional, but must be used if module is relative.
        :type package: str

        .. seealso::
            :func:`importlib.import_module`
        """
        # TODO: 3 ways to add a data source
        # (1) this way
        # (2) using class factory, inputs in JSON file
        # (3) use DataSource or one of its subclasses
        # import module
        mod = importlib.import_module(module, package)
        # get data source class definition from the module
        if data_source.startswith('_'):
                err_msg = 'No "%s" attribute in "%s".' % (data_source, mod)
                raise AttributeError(err_msg)
        self.data_sources[data_source] = getattr(mod, data_source)
        # only update layer info if it is missing!
        if data_source not in self.layer:
            # copy data source parameters to :attr:`Layer.layer`
            self.layer[data_source] = {'module': module, 'package': package}
        # add a place holder for the data source object when it's constructed
        self.data_obj[data_source] = None

    def open(self, data_source, filename, path=None):
        """
        Open filename to get data for data_source.

        :param data_source: Data source for which the file contains data.
        :type data_source: str
        :param filename: Name of the file which contains data for the data
            source.
        :type filename: str
        :param path: Path of file containting data. [../data]
        :type path: str
        """
        # default path for data is in ../data
        if not path:
            path = os.path.join(_DATA, data_source)
        # only update layer info if it is missing!
        if data_source not in self.layer:
            # update path and filename to this layer of the model
            self.layer[data_source] = {'path': path, 'filename': filename}
        # filename can be a list or a string, concatenate list with os.pathsep
        # and append the full path to strings.
        if isinstance(filename, basestring):
            filename = os.path.join(path, filename)
        else:
            file_list = [os.path.join(path, f) for f in filename]
            filename = os.path.pathsep.join(file_list)
        # call constructor of data source with filename argument
        self.data_obj[data_source] = self.data_sources[data_source](filename)
        # register data and uncertainty in registry
        data_src_obj = self.data_obj[data_source]
        self.data.register(data_src_obj.data, data_src_obj.uncertainty,
                           data_src_obj.isconstant, data_src_obj.timeseries,
                           data_src_obj.data_source)

    def load(self):
        """
        Add data_sources to layer and open files with data for the data_source.
        """
        for k, v in self.layer.iteritems():
            self.add(k, v['module'], v.get('package'))
            if v.get('filename'):
                self.open(k, v['filename'], v.get('path'))

    def edit(self, data_src, value):
        """
        Edit data layer.

        :param data_src: Name of :class:`DataSource` to edit.
        :type data_scr: str
        :param value: Values to edit.
        :type value: dict
        """
        # check if opening file
        if 'filename' in value:
#             items = self.data_obj[data_src].data.keys()  # items to edit
            items = [k for k, v in self.data.data_source.iteritems() if
                     v == data_src]
            self.data.unregister(items)  # remove items from Registry
            # open file and register new data
            self.open(data_src, value['filename'], value.get('path'))
            self.layer[data_src].update(value)  # update layer with new items

    def delete(self, data_src):
        """
        Delete data sources.
        """
        items = self.data_obj[data_src].data.keys()  # items to edit
        self.data.unregister(items)  # remove items from Registry
        self.layer.pop(data_src)  # remove data source from layer
        self.data_obj.pop(data_src)  # remove data_source object
        self.data_sources.pop(data_src)  # remove data_source object


# TODO: refactor layers to remove redundancy!!!
class Formulas(Layer):
    """
    Layer containing formulas.
    """
    def __init__(self, formulas=None):
        super(Formulas, self).__init__(formulas)
        #: dictionary of formula sources added to the Formula layer
        self.formula_sources = {}
        #: formula source objects
        self.formula_obj = {}
        #: formulas
        self.formulas = FormulaRegistry()
        # layers are initialized by the model

    def add(self, formula_source, module, package=None):
        """
        Import module (from package) with formulas, import formulas and add
        them to formula registry.

        :param formula_source: Name of the formula source to add/open.
        :param module: Module containing formula source.
        :param package: [Optional] Package of formula source module.

        .. seealso::
            :func:`importlib.import_module`
        """
        # import module
        mod = importlib.import_module(module, package)
        # get formula source class definition from module
        if formula_source.startswith('_'):
                err_msg = 'No "%s" attribute in "%s".' % (formula_source, mod)
                raise AttributeError(err_msg)
        self.formula_sources[formula_source] = getattr(mod, formula_source)
        # only update layer info if it is missing!
        if formula_source not in self.layer:
            # copy formula source parameters to :attr:`Layer.layer`
            self.layer[formula_source] = {'module': module, 'package': package}
        self.formula_obj[formula_source] = \
            self.formula_sources[formula_source]()
        # register formula and linearity in registry
        formula_src_obj = self.formula_obj[formula_source]
        self.formulas.register(formula_src_obj.formulas,
                               formula_src_obj.islinear)

    def open(self, formula_source, module, package=None):
        self.add(formula_source, module, package=None)

    def load(self):
        """
        Add formula_source to layer.
        """
        for k, v in self.layer.iteritems():
            self.add(k, v['module'], v.get('package'))


class Calculation(Layer):
    """
    Layer containing formulas.
    """
    def __init__(self, degmodes=None):
        super(Calculation, self).__init__(degmodes)
        #: dictionary of degradation sources added to the Formula layer
        self.deg_sources = {}
        #: degradation source objects
        self.degmode_obj = {}
        #: degradation modes
        self.degmodes = CalcRegistry()
        # layers are initialized by the model

    def add(self, deg_source, module, package=None):
        """
        """
        # import module
        mod = importlib.import_module(module, package)
        # get degradation source class definition from module
        if deg_source.startswith('_'):
                err_msg = 'No "%s" attribute in "%s".' % (deg_source, mod)
                raise AttributeError(err_msg)
        self.deg_sources[deg_source] = getattr(mod, deg_source)
        # instantiate the degmode object
        self.degmode_obj[deg_source] = self.deg_sources[deg_source]()
        # register degmode and dependencies in registry
        deg_src_obj = self.degmode_obj[deg_source]
        self.degmodes.register({deg_source: deg_src_obj},
                               {deg_source: deg_src_obj.dependencies},
                               {deg_source: deg_src_obj.always_calc},
                               {deg_source: deg_src_obj.frequency})

    def open(self, deg_source, module, package=None):
        self.add(deg_source, module, package=None)

    def load(self):
        """
        Add deg_source to layer.
        """
        for k, v in self.layer.iteritems():
            self.add(k, v['module'], v.get('package'))


class Outputs(Layer):
    """
    Layer containing outputs.
    """
    def __init__(self, outputs=None):
        super(Outputs, self).__init__(outputs)
        #: dictionary of output sources added to the Formula layer
        self.output_sources = {}
        #: output source objects
        self.output_obj = {}
        #: outputs
        self.outputs = OutputRegistry()
        # layers are initialized by the model

    def add(self, output_sources, module, package=None):
        """
        """
        # import module
        mod = importlib.import_module(module, package)
        # get output source class definition from module
        if output_sources.startswith('_'):
                err_msg = 'No "%s" attribute in "%s".' % (output_sources, mod)
                raise AttributeError(err_msg)
        self.output_sources[output_sources] = getattr(mod, output_sources)
        # instantiate the output object
        self.output_obj[output_sources] = self.output_sources[output_sources]()
        # register outputs and meta-data in registry
        out_src_obj = self.output_obj[output_sources]
        self.outputs.register(out_src_obj.outputs, out_src_obj.initial_value,
                              out_src_obj.size, out_src_obj.uncertainty,
                              out_src_obj.isconstant, out_src_obj.isproperty)

    def open(self, output_source, module, package=None):
        self.add(output_source, module, package=None)

    def load(self):
        """
        Add output_source to layer.
        """
        for k, v in self.layer.iteritems():
            self.add(k, v['module'], v.get('package'))


class Simulation(Layer):
    """
    Layer containing simulation related info.
    """
    def __init__(self, simulation=None):
        super(Simulation, self).__init__(simulation)
        self.sim_src = {}
        self.sim_obj = {}
        self.simulation = Registry()

    def add(self, sim_src, module, package=None):
        """
        """
        # import module
        mod = importlib.import_module(module, package)
        if sim_src.startswith('_'):
                err_msg = 'No "%s" attribute in "%s".' % (sim_src, mod)
                raise AttributeError(err_msg)
        self.sim_src[sim_src] = getattr(mod, sim_src)

    def open(self, sim_src, filename, path=None):
        # default path for data is in ../simulations
        if not path:
            path = os.path.join(_SIMULATIONS, sim_src)
        filename = os.path.join(path, filename)
        # call constructor of sim source with filename argument
        self.sim_obj[sim_src] = self.sim_src[sim_src](filename)
        # register simulation in registry, the only reason to register an item
        # is make sure it doesn't overwrite other items
        self.simulation.register({sim_src: self.sim_obj[sim_src]})

    def load(self):
        """
        Add sim_src to layer.
        """
        for k, v in self.layer.iteritems():
            self.add(k, v['module'], v.get('package'))
            self.open(k, v['filename'], v.get('path'))
