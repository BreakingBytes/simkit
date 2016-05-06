# -*- coding: utf-8 -*-
"""
This is the Carousel model module. The model module contains the definition
for the Model class. In general a Model contains Layers.

The Carousel model contains five layers:
:class:`~carousel.core.layers.Data`,
:class:`~carousel.core.layers.Formulas`,
:class:`~carousel.core.layers.Calculation`,
:class:`~carousel.core.layers.Outputs` and
:class:`~carousel.core.layers.Simulation`. The
:class:`~carousel.core.layers.Data` layer organizes
:ref:`data-sources` by providing methods to add and load data for Carousel.
The :class:`~carousel.core.layers.Formulas` layer loads
:ref:`formulas` used by :class:`~carousel.core.layers.Calculation`
calculations. The :class:`~carousel.core.layers.Outputs` layer
organizes the calculated outputs for use in other calculations. Finally the
:class:`~carousel.core.layers.Simulation` layer organizes
options such as how long the simulation should run and takes care of actually
running the simulation.
"""

import importlib
import json
import os
from carousel.core import logging, _listify

LOGGER = logging.getLogger(__name__)
LAYERS_MOD = '.layers'
LAYERS_PKG = 'carousel.core'


class Model(object):
    """
    A class for models. Carousel is a subclass of the :class:`Model` class.

    :param modelfile: The name of the json file to load.
    :type modelfile: str
    :param layers_mod: The name of module with layer class definitions.
    :type layers_mod: str
    :param layers_pkg: Optional package with layers module. [None]
    :type layers_pkg: str
    """
    def __init__(self, modelfile, layers_mod, layers_pkg=None,
                 layer_cls_names=NotImplemented, commands=NotImplemented):
        #: model file
        self.modelfile = os.path.abspath(modelfile)
        #: model path, layer files relative to model
        self.modelpath = os.path.dirname(self.modelfile)
        #: dictionary of the model
        self.model = None
        #: dictionary of layer class names
        self.layer_cls_names = layer_cls_names
        #: dictionary of model layer classes
        self.layers = {}
        #: list of model commands
        self.commands = commands
        self._initialize(modelfile, layers_mod, layers_pkg)  # initialize

    @property
    def state(self):
        """
        current state of the model
        """
        return self.get_state()

    def _load(self, modelfile, layer=None):
        """
        Load or update all or part of :attr:`model`.

        :param modelfile: The name of the json file to load.
        :type modelfile: str
        :param layer: Optionally load only specified layer.
        :type layer: str
        """
        # open model file for reading and convert JSON object to dictionary
        with open(modelfile, 'r') as fp:
            _model = json.load(fp)
        # if layer argument spec'd then only update/load spec'd layer
        if not layer or not self.model:
            # update/load model if layer not spec'd or if no model exists yet
            self.model = _model
        else:
            # convert non-sequence to tuple
            layers = layer if isinstance(layer, (list, tuple)) else (layer, )
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
            layers = layer if isinstance(layer, (list, tuple)) else (layer, )
        for layer in layers:
            # relative path to layer files from model file
            path = os.path.abspath(os.path.join(self.modelpath, '..', layer))
            getattr(self, layer).load(path)

    def _initialize(self, modelfile, layers_mod, layers_pkg):
        """
        Initialize model and layers.

        :param modelfile: The name of the JSON file with model data.
        :type modelfile: str
        :param layers_mod: The name of module with layer class definitions.
        :type layers_mod: str
        :param layers_pkg: Optional package with layers module. [None]
        :type layers_pkg: str
        """
        # read modelfile, convert JSON and load/update model
        self._load(modelfile)
        # initialize layers
        mod = importlib.import_module(layers_mod, layers_pkg)  # module
        for layer, value in self.model.iteritems():
            # from layers module get the layer's class definition
            layer_cls = getattr(mod, self.layer_cls_names[layer])  # class def
            self.layers[layer] = layer_cls  # add layer class def to model
            # set layer attribute with model data
            if hasattr(self, layer):
                setattr(self, layer, layer_cls(value))
            else:
                raise AttributeError('missing layer!')
        self._update()

    def load(self, modelfile, layer=None):
        """
        Load or update a model or layers in a model.

        :param modelfile: The name of the json file to load.
        :type modelfile: str
        :param layer: Optionally load only specified layer.
        :type layer: str
        """
        # read modelfile, convert JSON and load/update model
        self._load(modelfile, layer)
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

    def command(self, cmd, progress_hook, *args, **kwargs):
        """
        Call a model command. Must be implemented by each model.

        :raises: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    def get_state(self):
        """
        Getter method for state property. Must be implemented by each model.

        :returns: Current state of model.
        :raises: :exc:`NotImplementedError`
        """
        raise NotImplementedError


class BasicModel(Model):
    """
    A class for the BasicModel model.

    :param modelfile: The name of the json file to load.
    :type modelfile: str
    """
    def __init__(self, modelfile):
        #: valid layers
        layer_cls_names = {'data': 'Data', 'calculations': 'Calculation',
                           'formulas': 'Formulas', 'outputs': 'Outputs',
                           'simulations': 'Simulation'}
        commands = ['start', 'pause']
        self.data = None
        self.formulas = None
        self.calculations = None
        self.outputs = None
        self.simulations = None
        super(BasicModel, self).__init__(modelfile, LAYERS_MOD, LAYERS_PKG,
                                         layer_cls_names=layer_cls_names,
                                         commands=commands)
        # add time-step, dt, to data registry

    def get_state(self):
        """
        Validate the current model. This is a place holder.

        :returns: Current state of model.
        """
        if all([getattr(self, layer) for layer in self.layers]):
            return "Ready!"
        else:
            return "Some layers not loaded."

    def command(self, cmd, progress_hook=None, *args, **kwargs):
        """
        Execute a model command.

        :param cmd: Name of the command.
        :param progress_hook: A function to which progress updates are passed.
        """
        cmds = cmd.split(None, 1)  # split commands and simulations
        sim_names = cmds[1:]  # simulations
        if not sim_names:
            sim_names = self.model['simulations'].iterkeys()
        if cmd not in self.commands:
            raise(Exception('"%" is not a model command.'))
        if cmd.lower() == 'start':
            kwargs = {'data_reg': self.data.data,
                      'formula_reg': self.formulas.formulas,
                      'calc_reg': self.calculations.calcs,
                      'out_reg': self.outputs.outputs,
                      'progress_hook': progress_hook}
            for sim_name in sim_names:
                self.simulations.simulations[sim_name].start(**kwargs)
        elif cmd.lower() == 'pause':
            for sim_name in sim_names:
                self.simulations.simulations[sim_name].pause()
