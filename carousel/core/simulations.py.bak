# -*- coding: utf-8 -*-
"""
This is the Simulation module. The Simulation layer takes of creating output
variables, writing data to disk, iterating over data and calculations at
each interval in the simulation and setting any parameters required to perform
the simulation. It gets all its info from the model, which in turn gets it from
each layer which gets info from the layers' sources.
"""

from carousel.core import logging, CommonBase, Registry, UREG, Q_, Parameter
from carousel.core.exceptions import CircularDependencyError, MissingDataError
import json
import errno
import os
import sys
import numpy as np
import Queue
import functools
from datetime import datetime

LOGGER = logging.getLogger(__name__)


def mkdir_p(path):
    """
    http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    :param path: path to make recursively
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise exc


def id_maker(obj):
    """
    Makes an ID from the object's class name and the datetime now in ISO format.

    :param obj: the class from which to make the ID
    :return: ID
    """
    dtfmt = '%Y%m%d-%H%M%S'
    return '%s-%s' % (obj.__class__.__name__, datetime.now().strftime(dtfmt))


def sim_progress_hook(format_args, display_header=False):
    if isinstance(format_args, basestring):
        format_str = '---------- %s ----------\n'
    else:
        idx = format_args[0]
        fields, values = zip(*format_args[1:])
        format_str = '\r%5d' + ' %10.4g' * len(values)
        if display_header:
            units = (str(v.dimensionality) for v in values)
            units = tuple(['n/d' if u == 'dimensionless' else u
                           for u in units])
            format_args = fields + units + (idx,) + values
            format_units = ('units' + ' %10s' * len(units)) + '\n'
            fmt_header = ('index' + ' %10s' * len(fields)) + '\n'
            format_str = fmt_header + format_units + format_str
        else:
            format_args = (idx,) + values
    sys.stdout.write(format_str % format_args)


def topological_sort(dag):
    """
    topological sort

    :param dag: directed acyclic graph
    :type dag: dict

    .. seealso:: `Topographical Sorting
        <http://en.wikipedia.org/wiki/Topological_sorting>`_,
        `Directed Acyclic Graph (DAG)
        <https://en.wikipedia.org/wiki/Directed_acyclic_graph>`_
    """
    # find all edges of dag
    topsort = [node for node, edge in dag.iteritems() if not edge]
    # loop through nodes until topologically sorted
    while len(topsort) < len(dag):
        num_nodes = len(topsort)  # number of nodes
        # unsorted nodes
        for node in dag.viewkeys() - set(topsort):
            # nodes with no incoming edges
            if set(dag[node]) <= set(topsort):
                topsort.append(node)
                break
        # circular dependencies
        if len(topsort) == num_nodes:
            raise CircularDependencyError(dag.viewkeys() - set(topsort))
    return topsort


class SimParameter(Parameter):
    _attrs = ['ID', 'path', 'commands', 'data', 'thresholds', 'interval',
              'sim_length', 'display_frequency', 'display_fields',
              'write_frequency', 'write_fields']


class SimRegistry(Registry):
    """
    Registry for simulations.
    """
    #: meta names
    meta_names = ['commands']

    def register(self, sim, *args, **kwargs):
        """
        register simulation and metadata.

        * ``commands`` - list of methods to callable from model

        :param sim: new simulation
        """
        kwargs.update(zip(self.meta_names, args))
        # call super method, now meta can be passed as args or kwargs.
        super(SimRegistry, self).register(sim, **kwargs)


class SimBase(CommonBase):
    """
    Meta class for simulations.
    """
    _path_attr = 'sim_path'
    _file_attr = 'sim_file'
    _attributes = 'attrs'
    _deprecated = 'deprecated'
    _param_cls = SimParameter

    def __new__(mcs, name, bases, attr):
        # use only with Simulation subclasses
        if not CommonBase.get_parents(bases, SimBase):
            LOGGER.debug('bases:\n%r', bases)
            return super(SimBase, mcs).__new__(mcs, name, bases, attr)
        # set _meta combined from bases
        attr = mcs.set_meta(bases, attr)
        # let some attributes in subclasses be override super
        attributes = attr.pop(mcs._attributes, None)
        deprecated = attr.pop(mcs._deprecated, None)
        # set param file full path if simulations path and file specified or
        # try to set parameters from class attributes except private/magic
        attr = mcs.set_param_file_or_parameters(attr)
        # reset subclass attributes
        if attributes is not None:
            attr[mcs._attributes] = attributes
        if deprecated is not None:
            attr[mcs._deprecated] = deprecated
        LOGGER.debug('attibutes:\n%r', attr)
        return super(SimBase, mcs).__new__(mcs, name, bases, attr)


class Simulation(object):
    """
    A class for simulations.

    :param simfile: Filename of simulation configuration file.
    :type simfile: str
    :param settings: keyword name of simulation parameter to use for settings
    :type str:

    Simulation attributes can be passed directly as keyword arguments directly
    to :class:`~carousel.core.simulations.Simulation` or in a JSON file or as
    class attributes in a subclass or a combination of all 3 methods.

    To get a list of :class:`~carousel.core.simulations.Simulation` attributes
    and defaults get the :attr:`~carousel.core.simulations.Simulation.attrs`
    attribute.

    Any additional settings provided as keyword arguments will override settings
    from file.
    """
    __metaclass__ = SimBase
    attrs = {
        'ID': None,
        'path': os.path.join('~', 'Carousel', 'Simulations'),
        'commands': ['start', 'pause'],
        'data': None,
        'thresholds': None,
        'interval': 1 * UREG.hour,
        'sim_length': 1 * UREG.year,
        'display_frequency': 1,
        'display_fields': None,
        'write_frequency': 8760,
        'write_fields': None
    }
    deprecated = {
        'interval': 'interval_length',
        'sim_length': 'simulation_length'
    }

    def __init__(self, simfile=None, settings=None, **kwargs):
        # load simfile if it's an argument
        if simfile is not None:
            # read and load JSON parameter map file as "parameters"
            self.param_file = simfile
            with open(self.param_file, 'r') as param_file:
                file_params = json.load(param_file)
                #: simulation parameters from file
                self.parameters = {settings: SimParameter(**params) for
                                   settings, params in file_params.iteritems()}
        # if not subclassed and metaclass skipped, then use kwargs
        if not hasattr(self, 'parameters'):
            #: parameter file
            self.param_file = None
            #: simulation parameters from keyword arguments
            self.parameters = kwargs
        else:
            # use first settings
            if settings is None:
                self.settings, self.parameters = self.parameters.items()[0]
            else:
                #: name of sim settings used for parameters
                self.settings = settings
                self.parameters = self.parameters[settings]
            # use any keyword arguments instead of parameters
            self.parameters.update(kwargs)
        # make pycharm happy - attributes assigned in loop by attrs
        self.thresholds = {}
        self.display_frequency = 0
        self.display_fields = {}
        self.write_frequency = 0
        self.write_fields = {}
        # pop deprecated attribute names
        for k, v in self.deprecated.iteritems():
            val = self.parameters['extras'].pop(v, None)
            # update parameters if deprecated attr used and no new attr
            if val and k not in self.parameters:
                self.parameters[k] = val
        # Attributes
        for k, v in self.attrs.iteritems():
            setattr(self, k, self.parameters.get(k, v))
        # member docstrings are in documentation since attrs are generated
        if self.ID is None:
            # generate id from object class name and datetime in ISO format
            self.ID = id_maker(self)
        if self.path is not None:
            # expand environment variables, ~ and make absolute path
            self.path = os.path.expandvars(os.path.expanduser(self.path))
            self.path = os.path.abspath(self.path)
        # convert simulation interval to Pint Quantity
        if isinstance(self.interval, basestring):
            self.interval = UREG(self.interval)
        elif not isinstance(self.interval, Q_):
            self.interval = self.interval[0] * UREG(str(self.interval[1]))
        # convert simulation length to Pint Quantity
        if isinstance(self.sim_length, basestring):
            self.sim_length = UREG(self.sim_length)
        elif not isinstance(self.sim_length, Q_):
            self.sim_length = self.sim_length[0] * UREG(str(self.sim_length[1]))
        # convert simulation length to interval units to calc total intervals
        sim_to_interval_units = self.sim_length.to(self.interval.units)
        #: total number of intervals simulated
        self.number_intervals = np.ceil(sim_to_interval_units / self.interval)
        #: interval index, start at zero
        self.interval_idx = 0
        #: pause status
        self._ispaused = False
        #: finished status
        self._iscomplete = False
        #: initialized status
        self._isinitialized = False
        #: order of calculations
        self.calc_order = []
        #: command queue
        self.cmd_queue = Queue.Queue()
        #: index iterator
        self.idx_iter = self.index_iterator()
        #: data loaded status
        self._is_data_loaded = False

    @property
    def ispaused(self):
        """
        Pause property, read only. True if paused.
        """
        return self._ispaused

    @property
    def iscomplete(self):
        """
        Completion property, read only. True if finished.
        """
        return self._iscomplete

    @property
    def isinitialized(self):
        """
        Initialization property, read only. True if initialized.
        """
        return self._isinitialized

    @property
    def is_data_loaded(self):
        """
        Data loaded property, read only. True if data loaded.
        """
        return self._is_data_loaded

    def check_data(self, data):
        """
        Check if data loaded for all sources in data layer.

        :param data: data layer from model
        :type data: :class:`~carousel.core.layer.Data`
        :return: dictionary of data sources and objects or `None` if not loaded
        """
        data_objs = {
            data_src: data.objects.get(data_src) for data_src in data.layer
        }
        self._is_data_loaded = all(data_objs.values())
        return data_objs

    def initialize(self, calc_reg):
        """
        Initialize the simulation. Organize calculations by dependency.

        :param calc_reg: Calculation registry.
        :type calc_reg:
            :class:`~carousel.core.calculation.CalcRegistry`
        """
        self._isinitialized = True
        # TODO: if calculations are edited, loaded, added, etc. then reset
        self.calc_order = topological_sort(calc_reg.dependencies)

    def index_iterator(self):
        """
        Generator that resumes from same index, or restarts from sent index.
        """
        idx = 0  # index
        while idx < self.number_intervals:
            new_idx = yield idx
            idx += 1
            if new_idx:
                idx = new_idx - 1

    # TODO: change start to run

    def start(self, model, progress_hook=None):
        """
        Start the simulation from time zero.

        :param model: Model with layers and registries containing parameters
        :type: :class:`~carousel.core.models.Model`
        :param progress_hook: A function that receives either a string or a
            list containing the index followed by tuples of the data or outputs
            names and values specified by ``write_fields`` in the simfile.
        :type progress_hook: function


        The model registries should contain the following layer registries:
        * :class:`~carousel.core.data_sources.DataRegistry`,
        * :class:`~carousel.core.formulas.FormulaRegistry`,
        * :class:`~carousel.core.outputs.OutputRegistry`,
        * :class:`~carousel.core.calculation.CalcRegistry`
        """
        # check if data loaded
        data_objs = self.check_data(model.data)
        if not self.is_data_loaded:
            raise MissingDataError([ds for ds in data_objs if ds is None])
        # get layer registries
        data_reg = model.registries['data']
        formula_reg = model.registries['formulas']
        out_reg = model.registries['outputs']
        calc_reg = model.registries['calculations']
        # initialize
        if not self.isinitialized:
            self.initialize(calc_reg)
        # default progress hook
        if not progress_hook:
            progress_hook = functools.partial(
                sim_progress_hook, display_header=True
            )
        # start, resume or restart
        if self.ispaused:
            # if paused, then resume, do not resize outputs again.
            self._ispaused = False  # change pause state
            progress_hook('resume simulation')
        elif self.iscomplete:
            # if complete, then restart, do not resize outputs again.
            self._iscomplete = False  # change pause state
            progress_hook('restart simulation')
            self.idx_iter = self.index_iterator()
        else:
            # resize outputs
            # assumes that self.write_frequency is immutable
            # TODO: allow self.write_frequency to be changed
            # only resize outputs first time simulation is started
            # repeat output rows to self.write_frequency
            # put initial conditions of outputs last so it's copied when
            # idx == 0
            progress_hook('resize outputs')  # display progress
            for k in out_reg:
                if out_reg.isconstant[k]:
                    continue
                # repeat rows (axis=0)
                out_reg[k] = out_reg[k].repeat(self.write_frequency, 0)
                _initial_value = out_reg.initial_value[k]
                if not _initial_value:
                    continue
                if isinstance(_initial_value, basestring):
                    # initial value is from data registry
                    # assign in a scalar to a vector fills in the vector, yes!
                    out_reg[k][-1] = data_reg[_initial_value]
                else:
                    out_reg[k][-1] = _initial_value * out_reg[k].units
            progress_hook('start simulation')
        # check and/or make Carousel_Simulations and simulation ID folders
        mkdir_p(self.path)
        sim_id_path = os.path.join(self.path, self.ID)
        mkdir_p(sim_id_path)
        # header & units for save files
        data_fields = self.write_fields.get('data', [])  # any data fields
        out_fields = self.write_fields.get('outputs', [])  # any outputs fields
        save_header = tuple(data_fields + out_fields)  # concatenate fields
        # get units as strings from data & outputs
        data_units = [str(data_reg[f].dimensionality) for f in data_fields]
        out_units = [str(out_reg[f].dimensionality) for f in out_fields]
        save_units = tuple(data_units + out_units)  # concatenate units
        # string format for header & units
        save_str = ('%s' + ',%s' * (len(save_header) - 1)) + '\n'  # format
        save_header = (save_str * 2) % (save_header + save_units)  # header
        save_header = save_header[:-1]  # remove trailing new line
        # ===================
        # Static calculations
        # ===================
        progress_hook('static calcs')
        for calc in self.calc_order:
            if not calc_reg.is_dynamic[calc]:
                calc_reg.calculator[calc].calculate(
                    calc_reg[calc], formula_reg, data_reg, out_reg
                )
        # ====================
        # Dynamic calculations
        # ====================
        progress_hook('dynamic calcs')
        # TODO: assumes that interval size and indices are same, but should
        # interpolate for any size interval or indices
        for idx_tot in self.idx_iter:
            self.interval_idx = idx_tot  # update simulation interval counter
            idx = idx_tot % self.write_frequency
            # update properties
            for k, v in out_reg.isproperty.iteritems():
                # set properties from previous interval at night
                if v:
                    out_reg[k][idx] = out_reg[k][idx - 1]
            # night if any threshold exceeded
            if self.thresholds:
                night = not all(limits[0] < data_reg[data][idx] < limits[1] for
                                data, limits in self.thresholds.iteritems())
            else:
                night = None
            # daytime or always calculated outputs
            for calc in self.calc_order:
                # Determine if calculation is scheduled for this timestep
                # TODO: add ``start_at`` parameter combined with ``frequency``
                freq = calc_reg.frequency[calc]
                if not freq.dimensionality:
                    is_scheduled = (idx_tot % freq) == 0
                else:
                    # Frequency with units of time
                    is_scheduled = ((idx_tot * self.interval) % freq) == 0
                is_scheduled = (
                    is_scheduled and (not night or calc_reg.always_calc[calc])
                )
                if calc_reg.is_dynamic[calc] and is_scheduled:
                    calc_reg.calculator[calc].calculate(
                        calc_reg[calc], formula_reg, data_reg, out_reg,
                        timestep=self.interval, idx=idx
                    )
            # display progress
            if not (idx % self.display_frequency):
                progress_hook(self.format_progress(idx, data_reg, out_reg))
                # disp_head = False
            # create an index for the save file, 0 if not saving
            if not ((idx_tot + 1) % self.write_frequency):
                savenum = (idx_tot + 1) / self.write_frequency
            elif idx_tot == self.number_intervals - 1:
                # save file index should be integer!
                savenum = int(np.ceil((idx_tot + 1) /
                                      float(self.write_frequency)))
            else:
                savenum = 0  # not saving this iteration
            # save file to disk
            if savenum:
                savename = self.ID + '_' + str(savenum) + '.csv'  # filename
                savepath = os.path.join(sim_id_path, savename)  # path
                # create array of all data & outputs to save
                save_array = self.format_write(data_reg, out_reg, idx + 1)
                # save as csv using default format & turn comments off
                np.savetxt(savepath, save_array, delimiter=',',
                           header=save_header, comments='')
            try:
                cmd = self.cmd_queue.get_nowait()
            except Queue.Empty:
                continue
            if cmd == 'pause':
                self._ispaused = True
                return
        self._iscomplete = True  # change completion status

    def format_progress(self, idx, data_reg, out_reg):
        data_fields = self.display_fields.get('data', [])  # data fields
        data_args = [(f, data_reg[f][idx]) for f in data_fields]
        out_fields = self.display_fields.get('outputs', [])  # outputs fields
        out_args = [(f, out_reg[f][idx]) for f in out_fields]
        return [idx] + data_args + out_args

    def format_write(self, data_reg, out_reg, idx=None):
        data_fields = self.write_fields.get('data', [])  # any data fields
        data_args = [data_reg[f][:idx].reshape((-1, 1)) for f in data_fields]
        out_fields = self.write_fields.get('outputs', [])  # any outputs fields
        out_args = [out_reg[f][:idx] for f in out_fields]
        return np.concatenate(data_args + out_args, axis=1)

    def pause(self, progress_hook=None):
        """
        Pause the simulation. How is this different from stopping it? Maintain
        info sufficient to restart simulation. Sets ``is_paused`` to True.
        Will this state allow analysis? changing parameters? What can you do
        with a paused simulation?
        Should be capable of saving paused simulation for loading/resuming
        later, that is the main usage. EG: someone else need computer, or power
        goes out, so on battery backup quickly pause simulation, and save.
        Is save automatic? Should there be a parameter for auto save changed?
        """
        # default progress hook
        if progress_hook is None:
            progress_hook = sim_progress_hook
        progress_hook('simulation paused')
        self.cmd_queue.put('pause')
        self._ispaused = True

    def load(self, model, progress_hook=None, *args, **kwargs):
        # default progress hook
        if progress_hook is None:
            progress_hook = sim_progress_hook
        data = kwargs.get('data', {})
        if not data and args:
            data = args[0]
        for k, v in data.iteritems():
            progress_hook('loading simulation for %s' % k)
            model.data.open(k, **v)
        self.check_data(model.data)

    def run(self, model, progress_hook=None, *args, **kwargs):
        # default progress hook
        if progress_hook is None:
            progress_hook = sim_progress_hook
        progress_hook('running simulation')
        self.load(model, progress_hook, *args, **kwargs)
        self.start(model, progress_hook)
