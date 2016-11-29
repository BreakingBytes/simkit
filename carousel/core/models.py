# -*- coding: utf-8 -*-
"""
This is the Carousel :mod:`~carousel.core.models` module that contains
definitions for the :class:`~carousel.core.models.Model` class.

The Carousel model contains five layers:
:class:`~carousel.core.layers.Data`,
:class:`~carousel.core.layers.Formulas`,
:class:`~carousel.core.layers.Calculations`,
:class:`~carousel.core.layers.Outputs` and
:class:`~carousel.core.layers.Simulations`. The
:class:`~carousel.core.layers.Data` layer organizes
:ref:`data-sources` by providing methods to add and load data for Carousel.
The :class:`~carousel.core.layers.Formulas` layer loads
:ref:`formulas` used by :class:`~carousel.core.layers.Calculations`
calculations. The :class:`~carousel.core.layers.Outputs` layer
organizes the calculated outputs for use in other calculations. Finally the
:class:`~carousel.core.layers.Simulations` layer organizes
options such as how long the simulation should run and takes care of actually
running the simulation.
"""

import importlib
import json
import os
import copy
from carousel.core import logging, _listify, CommonBase, Parameter

LOGGER = logging.getLogger(__name__)
LAYERS_MOD = '.layers'
LAYERS_PKG = 'carousel.core'
LAYER_CLS_NAMES = {'data': 'Data', 'calculations': 'Calculations',
                   'formulas': 'Formulas', 'outputs': 'Outputs',
                   'simulations': 'Simulations'}


class ModelParameter(Parameter):
    _attrs = ['layer', 'module', 'package', 'path', 'sources']


class ModelBase(CommonBase):
    """
    Base model meta class. If model has class attributes "modelpath" and
    "modelfile" then layer class names and model configuration will be read from
    the file on that path. Otherwise layer class names will be read from the
    class attributes.
    """
    _path_attr = 'modelpath'
    _file_attr = 'modelfile'
    _param_cls = ModelParameter
    _layers_cls_attr = 'layer_cls_names'
    _layers_mod_attr = 'layers_mod'
    _layers_pkg_attr = 'layers_pkg'
    _cmd_layer_attr = 'cmd_layer_name'
    _attr_default = {
        _layers_cls_attr: LAYER_CLS_NAMES, _layers_mod_attr: LAYERS_MOD,
        _layers_pkg_attr: LAYERS_PKG, _cmd_layer_attr: 'simulations'
    }

    def __new__(mcs, name, bases, attr):
        # use only with Model subclasses
        if not CommonBase.get_parents(bases, ModelBase):
            return super(ModelBase, mcs).__new__(mcs, name, bases, attr)
        attr = mcs.set_meta(bases, attr)
        # set param file full path if data source path and file specified or
        # try to set parameters from class attributes except private/magic
        attr = mcs.set_param_file_or_parameters(attr)
        # set default meta attributes
        meta = attr[mcs._meta_attr]
        for ma, dflt in mcs._attr_default.iteritems():
            a = getattr(meta, ma, None)
            if a is None:
                setattr(meta, ma, dflt)
        return super(ModelBase, mcs).__new__(mcs, name, bases, attr)


class Model(object):
    """
    A class for models. Carousel is a subclass of the :class:`Model` class.

    :param modelfile: The name of the JSON file with model data.
    :type modelfile: str
    """
    __metaclass__ = ModelBase

    def __init__(self, modelfile=None):
        meta = getattr(self, ModelBase._meta_attr)
        parameters = getattr(self, ModelBase._param_attr)
        # load modelfile if it's an argument
        if modelfile is not None:
            #: model file
            self.param_file = os.path.abspath(modelfile)
            LOGGER.debug('modelfile: %s', modelfile)
        else:
            modelfile = self.param_file
        # check meta class for model if declared inline
        if parameters:
            # TODO: separate model and parameters according to comments in #78
            #: dictionary of the model
            self.model = model = copy.deepcopy(parameters)
        else:
            #: dictionary of the model
            self.model = model = None
        # layer attributes initialized in meta class or _initialize()
        # for k, v in layer_cls_names.iteritems():
        #     setattr(self, k, v)
        # XXX: this seems bad to initialize attributes outside of constructor
        #: dictionary of model layer classes
        self.layers = {}
        #: state of model, initialized or uninitialized
        self._state = 'uninitialized'
        # need either model file or model and layer class names to initialize
        ready_to_initialize = ((modelfile is not None or model is not None) and
                               meta.layer_cls_names is not None)
        if ready_to_initialize:
            self._initialize()  # initialize using modelfile or model

    @property
    def state(self):
        """
        current state of the model
        """
        return self._state

    def _load(self, layer=None):
        """
        Load or update all or part of :attr:`model`.

        :param layer: Optionally load only specified layer.
        :type layer: str
        """
        # open model file for reading and convert JSON object to dictionary
        # read and load JSON parameter map file as "parameters"
        with open(self.param_file, 'r') as param_file:
            file_params = json.load(param_file)
            for layer, params in file_params.iteritems():
                # update parameters from file
                self.parameters[layer] = ModelParameter(**params)
        # if layer argument spec'd then only update/load spec'd layer
        if not layer or not self.model:
            # update/load model if layer not spec'd or if no model exists yet
            # TODO: separate model and parameters according to comments in #78
            self.model = copy.deepcopy(self.parameters)
        else:
            # convert non-sequence to tuple
            layers = _listify(layer)
            # update/load layers
            for layer in layers:
                self.model[layer] = copy.deepcopy(self.parameters[layer])

    def _update(self, layer=None):
        """
        Update layers in model.
        """
        meta = getattr(self, ModelBase._meta_attr)
        if not layer:
            layers = self.layers
        else:
            # convert non-sequence to tuple
            layers = _listify(layer)
        for layer in layers:
            # relative path to layer files from model file
            path = os.path.abspath(os.path.join(meta.modelpath, layer))
            getattr(self, layer).load(path)

    def _initialize(self):
        """
        Initialize model and layers.
        """
        meta = getattr(self, ModelBase._meta_attr)
        # read modelfile, convert JSON and load/update model
        if self.param_file is not None:
            self._load()
        LOGGER.debug('model:\n%r', self.model)
        # initialize layers
        # FIXME: move import inside loop for custom layers in different modules
        mod = importlib.import_module(meta.layers_mod, meta.layers_pkg)
        src_model = {}
        for layer, value in self.model.iteritems():
            # from layers module get the layer's class definition
            layer_cls = getattr(mod, meta.layer_cls_names[layer])  # class def
            self.layers[layer] = layer_cls  # add layer class def to model
            # check if model layers are classes
            src_value = {}  # layer value generated from source classes
            for src in value['sources']:
                # check if source has keyword arguments
                try:
                    src, kwargs = src
                except (TypeError, ValueError):
                    kwargs = {}  # no key work arguments
                # skip if not a source class
                if isinstance(src, basestring):
                    continue
                # generate layer value from source class
                src_value[src.__name__] = {'module': src.__module__,
                                           'package': None}
                # update layer keyword arguments
                src_value[src.__name__].update(kwargs)
            # use layer values generated from source class
            if src_value:
                value = src_model[layer] = src_value
            else:
                srcmod, srcpkg = value.get('module'), value.get('package')
                try:
                    value = dict(value['sources'])
                except ValueError:
                    value = dict.fromkeys(value['sources'], {})
                for src in value.viewkeys():
                    if srcmod is not None:
                        value[src]['module'] = srcmod
                    if srcpkg is not None:
                        value[src]['package'] = srcpkg
            # set layer attribute with model data
            setattr(self, layer, layer_cls(value))
        # update model with layer values generated from source classes
        if src_model:
            self.model.update(src_model)
        self._update()
        self._state = 'initialized'

    def load(self, modelfile, layer=None):
        """
        Load or update a model or layers in a model.

        :param modelfile: The name of the json file to load.
        :type modelfile: str
        :param layer: Optionally load only specified layer.
        :type layer: str
        """
        # read modelfile, convert JSON and load/update model
        self.param_file = modelfile
        self._load(layer)
        self._update(layer)

    def edit(self, layer, item, delete=False):
        """
        Edit model.

        :param layer: Layer of model to edit
        :type layer: str
        :param item: Items to edit.
        :type item: dict
        :param delete: Flag to return
            :class:`~carousel.core.layers.Layer` to delete item.
        :type delete: bool
        """
        # get layer attribute with model data
        if hasattr(self, layer):
            layer_obj = getattr(self, layer)
        else:
            raise AttributeError('missing layer: %s', layer)
        if delete:
            return layer_obj
        # iterate over items and edit layer
        for k, v in item.iteritems():
            if k in layer_obj.layer:
                layer_obj.edit(k, v)  # edit layer
            else:
                raise AttributeError('missing layer item: %s', k)
            # update model data
            if k in self.model[layer]:
                self.model[layer][k].update(v)
            else:
                raise AttributeError('missing model layer item: %s', k)

    def add(self, layer, items):
        """
        Add items in model.
        """
        for k in items.iterkeys():
            if k in self.model[layer]:
                raise Exception('item %s is already in layer %s' % (k, layer))
        self.model[layer].update(items)
        # this should also update Layer.layer, the layer data
        # same as calling layer constructor
        # so now just need to add items to the layer
        for k, v in items.iteritems():
            getattr(self, layer).add(k, v['module'], v.get('package'))

    def delete(self, layer, items):
        """
        Delete items in model.
        """
        # Use edit to get the layer obj containing item
        items = _listify(items)  # make items a list if it's not
        layer_obj = self.edit(layer, dict.fromkeys(items), delete=True)
        for k in items:
            if k in layer_obj.layer:
                layer_obj.delete(k)
            else:
                raise AttributeError('item %s missing from layer %s' %
                                     (k, layer))
            # don't need to pop items from self.model, because, self.layer
            # points to the same object as the item in model!
            # for example:
            #    (Pdb) id(self.model['data'])  # same ID as layer in data
            #    125639560L
            #    (Pdb) id(self.data.layer)  # same ID as data in model
            #    125639560L

    def save(self, modelfile, layer=None):
        """
        Save a model file.

        :param modelfile: The name of the json file to save.
        :type modelfile: str
        :param layer: Optionally save only specified layer.
        :type layer: str
        """
        if layer:
            obj = {layer: self.model[layer]}
        else:
            obj = self.model
        with open(modelfile, 'w') as fp:
            json.dump(obj, fp, indent=2, sort_keys=True)

    @property
    def registries(self):
        return {layer: getattr(self, layer).reg
                for layer in self.layers}

    @property
    def cmd_layer(self):
        meta = getattr(self, ModelBase._meta_attr)
        return getattr(self, meta.cmd_layer_name, NotImplemented)

    @property
    def commands(self):
        return self.cmd_layer.reg.commands

    def command(self, cmd, progress_hook=None, *args, **kwargs):
        """
        Execute a model command.

        :param cmd: Name of the command.
        :param progress_hook: A function to which progress updates are passed.
        """
        cmds = cmd.split(None, 1)  # split commands and simulations
        sim_names = cmds[1:]  # simulations
        if not sim_names:
            sim_names = self.cmd_layer.reg.iterkeys()
        for sim_name in sim_names:
            sim_cmd = getattr(self.cmd_layer.reg[sim_name], cmd)
            sim_cmd(self, progress_hook=progress_hook, *args, **kwargs)
