# -*- coding: utf-8 -*-
"""
This is the Simulation module. The Simulation layer takes of creating output
variables, writing data to disk, iterating over data and calculations at
each interval in the simulation and setting any parameters required to perform
the simulation. It gets all its info from the model, which in turn gets it from
each layer which gets info from the layers' sources.
"""

from carousel.core import UREG, Registry
from carousel.core.exceptions import CircularDependencyError
import json
import os
import sys
import numpy as np
import Queue
import functools


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


class SimRegistry(Registry):
    #: meta names
    _meta_names = ['commands']

    def __init__(self):
        super(SimRegistry, self).__init__()
        #: simulation commands
        self.commands = {}

    def register(self, sim, *args, **kwargs):
        kwargs.update(zip(self._meta_names, args))
        # call super method, now meta can be passed as args or kwargs.
        super(SimRegistry, self).register(sim, **kwargs)


class Simulation(object):
    """
    A class for simulations.

    :param simfile: Filename of simulation configuration file.
    :type simfile: str
    """
    def __init__(self, simfile):
        with open(simfile, 'r') as fp:
            #: parameters from file for simulation
            self.sim_params = json.load(fp)
        _path = self.sim_params.get('path', "~\\Carousel_Simulations\\")
        #: path where all Carousel simulation files are stored
        self.path = os.path.expandvars(os.path.expanduser(_path))
        #: ID for this particular simulation, used for path & file names
        self.ID = self.sim_params['ID']
        #: thresholds for calculations
        self.thresholds = self.sim_params.get('thresholds', {})
        # simulation intervals
        _interval = self.sim_params.get('interval_length', [1, 'hour'])
        #: length of each interval
        self.interval = _interval[0] * UREG[str(_interval[1])]
        _sim_length = self.sim_params.get('simulation_length', [25, 'years'])
        #: simulation length
        self.sim_length = _sim_length[0] * UREG[str(_sim_length[1])]
        # rescale simulation length to interval units to calc no. of intervals
        _sim_length = self.sim_length.to(self.interval.units)
        #: total number of intervals simulated
        self.number_intervals = np.ceil(_sim_length / self.interval)
        #: frequency output is displayed
        self.display_frequency = self.sim_params.get('display_frequency', 12)
        #: output fields displayed
        self.display_fields = self.sim_params.get('display_fields')
        # data dump
        #: frequency output is saved
        self.write_frequency = self.sim_params.get('write_frequency', 8760)
        #: output fields written to disk
        self.write_fields = self.sim_params.get('write_fields')
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
        #: commands
        self.commands = ['start', 'pause']

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

    def initialize(self, calc_reg):
        """
        Initialize the simulation. Organize calculations by dependency.

        :param calc_reg: Calculation registry.
        :type calc_reg:
            :class:`~carousel.core.calculation.CalcRegistry`
        """
        self._isinitialized = True
        # TODO: if calculations are editted, loaded, added, etc. then reset
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

    def start(self, data_reg, formula_reg, out_reg, calc_reg,
              progress_hook=None):
        """
        Start the simulation from time zero.

        :param data_reg: Data registry.
        :type data_reg:
            :class:`~carousel.core.data_sources.DataRegistry`
        :param formula_reg: Formula registry.
        :type formula_reg:
            :class:`~carousel.core.formulas.FormulaRegistry`
        :param out_reg: Outputs registry.
        :type out_reg:
            :class:`~carousel.core.outputs.OutputRegistry`
        :param calc_reg: Calculation registry.
        :type calc_reg:
            :class:`~carousel.core.calculation.CalcRegistry`
        :param progress_hook: A function that receives either a string or a
            list containing the index followed by tuples of the data or outputs
            names and values specified by ``write_fields`` in the simfile.
        :type progress_hook: function
        """
        # initialize
        if not self.isinitialized:
            self.initialize(calc_reg)
        # default progress hook
        if not progress_hook:
            _prog_hook = Simulation._progress_hook
            progress_hook = functools.partial(_prog_hook, display_header=True)
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
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        sim_id_path = os.path.join(self.path, self.ID)
        if not os.path.isdir(sim_id_path):
            os.mkdir(sim_id_path)
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
        # FIXME: static calcs may not have same topological order as dynamic
        # calcs, probably better to base sort on args instead of user definied
        # dependencies
        # Static calculations
        progress_hook('static calcs')
        for calc in self.calc_order:
            calc_reg[calc].calc_static(formula_reg, data_reg, out_reg,
                                       timestep=self.interval)
        # Dynamic calculations
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
            # night if any thresholds exceeded, False if empty
            night = any(limits[0] < data_reg[data][idx] < limits[1] for
                        data, limits in self.thresholds.iteritems())
            # daytime or always calculated outputs
            for calc in self.calc_order:
                if not night or calc_reg.always_calc[calc]:
                    calc_reg[calc].calc_dynamic(
                        idx, formula_reg, data_reg, out_reg,
                        timestep=self.interval
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

    @staticmethod
    def _progress_hook(format_args, display_header):
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
                format_args = fields + units + (idx, ) + values
                format_units = ('units' + ' %10s' * len(units)) + '\n'
                fmt_header = ('index' + ' %10s' * len(fields)) + '\n'
                format_str = fmt_header + format_units + format_str
            else:
                format_args = (idx, ) + values
        sys.stdout.write(format_str % format_args)

    def format_write(self, data_reg, out_reg, idx=None):
        data_fields = self.write_fields.get('data', [])  # any data fields
        data_args = [data_reg[f][:idx].reshape((-1, 1)) for f in data_fields]
        out_fields = self.write_fields.get('outputs', [])  # any outputs fields
        out_args = [out_reg[f][:idx] for f in out_fields]
        return np.concatenate(data_args + out_args, axis=1)

    def pause(self):
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
        self.cmd_queue.put('pause')
        self._ispaused = True

    # load and save are handled by the layer or model, not by simulations
    # sources!
