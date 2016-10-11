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
from carousel.core import logging, _listify, CommonBase

LOGGER = logging.getLogger(__name__)
LAYERS_MOD = '.layers'
LAYERS_PKG = 'carousel.core'


class ModelBase(CommonBase):
    """
    Base model meta class. If model has class attributes "modelpath" and
    "modelfile" then layer class names and model configuration will be read from
    the file on that path. Otherwise layer class names will be read from the
    class attributes.
    """
    _path_attr = 'modelpath'
    _file_attr = 'modelfile'
    _layers_cls_attr = 'layer_cls_names'

    def __new__(mcs, name, bases, attr):
        # use only with Model subclasses
        if not CommonBase.get_parents(bases, ModelBase):
            return super(ModelBase, mcs).__new__(mcs, name, bases, attr)
        # set model file full path if model path and file specified or
        # try to set parameters from class attributes except private/magic
        modelpath = attr.get(mcs._path_attr)  # path to models and layers
        modelfile = attr.pop(mcs._file_attr, None)  # model file
        layer_cls_names = attr.get(mcs._layers_cls_attr)
        # check bases for model parameters b/c attr doesn't include bases
        for base in bases:
            if layer_cls_names is None:
                layer_cls_names = getattr(base, mcs._layers_cls_attr, None)
            if modelpath is None:
                modelpath = getattr(base, mcs._path_attr, None)
            if modelfile is None:
                modelfile = getattr(base, mcs._file_attr, None)
        if None not in [modelpath, modelfile]:
            attr[mcs._file_attr] = os.path.join(modelpath, 'models', modelfile)
        elif layer_cls_names is not None:
            attr['model'] = dict.fromkeys(layer_cls_names)
            for k in attr['model']:
                attr['model'][k] = attr.pop(k, None)
        return super(ModelBase, mcs).__new__(mcs, name, bases, attr)


class Model(object):
    """
    A class for models. Carousel is a subclass of the :class:`Model` class.

    :param modelfile: The name of the JSON file with model data.
    :type modelfile: str
    """
    __metaclass__ = ModelBase
    # TODO: these should be in a Meta class
    #: dictionary of layer class names
    layer_cls_names = {'data': 'Data', 'calculations': 'Calculations',
                       'formulas': 'Formulas', 'outputs': 'Outputs',
                       'simulations': 'Simulations'}
    # FIXME: doesn't work for layers in different modules
    # TODO: should be dictionaries, combined with layer_cls_names and modelfile
    #: module with layer class definitions
    layers_mod = LAYERS_MOD
    #: package with layers module
    layers_pkg = LAYERS_PKG
    #: simulation layer
    cmd_layer_name = 'simulations'

    def __init__(self, modelfile=None):
        # check for modelfile in meta class, but use argument if not None
        if modelfile is None and hasattr(self, 'modelfile'):
            modelfile = self.modelfile
            modelpath = self.modelpath
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
            self.modelpath = os.path.dirname(os.path.dirname(self.modelfile))
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
                               self.layer_cls_names is not None)
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
            path = os.path.abspath(os.path.join(self.modelpath, layer))
            getattr(self, layer).load(path)

    def _initialize(self):
        """
        Initialize model and layers.
        """
        # read modelfile, convert JSON and load/update model
        if self.modelfile is not None:
            self._load()
        LOGGER.debug('model:\n%r', self.model)
        # initialize layers
        # FIXME: move import inside loop for custom layers in different modules
        mod = importlib.import_module(self.layers_mod, self.layers_pkg)
        src_model = {}
        for layer, value in self.model.iteritems():
            # from layers module get the layer's class definition
            layer_cls = getattr(mod, self.layer_cls_names[layer])  # class def
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
        return getattr(self, self.cmd_layer_name, NotImplemented)

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
