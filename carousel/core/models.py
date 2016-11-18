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
        # make model from parameters
        self.model = dict.fromkeys(meta.layer_cls_names)
        # check for modelfile in meta class, but use argument if not None
        if modelfile is None and hasattr(self, 'modelfile'):
            modelfile = self.modelfile
            modelpath = self._meta.modelpath
            LOGGER.debug('modelfile: %s', modelfile)
        else:
            # modelfile was either given as arg or wasn't in metaclass
            modelpath = None  # modelpath will be derived from modelfile
            #: model file
            self.modelfile = modelfile
        # get modelpath from modelfile if not in meta class
        if modelfile is not None and modelpath is None:
            self.modelfile = os.path.abspath(modelfile)
            #: model path, used to find layer files relative to model
            self._meta.modelpath = os.path.dirname(os.path.dirname(self.modelfile))
            modelpath = self._meta.modelpath  # update this field just in case
        # check meta class for model if declared inline
        if hasattr(self, 'model'):
            model = self.model
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
        with open(self.modelfile, 'r') as fp:
            _model = json.load(fp)
        # if layer argument spec'd then only update/load spec'd layer
        if not layer or not self.model:
            # update/load model if layer not spec'd or if no model exists yet
            self.model = _model
        else:
            # convert non-sequence to tuple
            layers = _listify(layer)
            # update/load layers
            for layer in layers:
                self.model[layer] = _model[layer]

    def _update(self, layer=None):
        """
        Update layers in model.
        """
        if not layer:
            layers = self.layers
        else:
            # convert non-sequence to tuple
            layers = _listify(layer)
        for layer in layers:
            # relative path to layer files from model file
            path = os.path.abspath(os.path.join(self._meta.modelpath, layer))
            getattr(self, layer).load(path)

    def _initialize(self):
        """
        Initialize model and layers.
        """
        meta = getattr(self, ModelBase._meta_attr)
        # read modelfile, convert JSON and load/update model
        if self.modelfile is not None:
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
            for src in value:
                # skip if not a source class
                if isinstance(src, basestring):
                    continue
                # check if source has keyword arguments
                try:
                    src, kwargs = src
                except TypeError:
                    kwargs = {}  # no key work arguments
                # generate layer value from source class
                src_value[src.__name__] = {'module': src.__module__,
                                           'package': None}
                # update layer keyword arguments
                src_value[src.__name__].update(kwargs)
            # use layer values generated from source class
            if src_value:
                value = src_model[layer] = src_value
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
        self.modelfile = modelfile
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
