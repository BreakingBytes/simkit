# -*- coding: utf-8 -*-

"""
This module provides base classes for calculations. All calculations should
inherit from one of the calcs in this module.
"""

import json
import os
from circus.core import _CALCS, Registry, UREG


class CalcRegistry(Registry):
    """
    A registry for calculations. Each key is a calculation. The value
    of each calculation is split into 2 dictionaries: "static" and
    "dynamic". Static calculations occur once at the beginning of a simulation
    and dynamic calculations occur at every interval. The contents of either
    the "static" or "dynamic" key is an ordered list of formulas, their
    arguments and return values.

    Calculation modes can have `dependencies <http://xkcd.com/754/>`_ that must
    be calculated first. Dependencies are listed as meta-data.
    """
    def __init__(self):
        super(CalcRegistry, self).__init__()
        #: dependencies calculated before the calculation listing them
        self.dependencies = {}
        #: ``True`` if always calculated (day and night)
        self.always_calc = {}
        #: frequency calculation is calculated in intervals or units of time
        self.frequency = {}

    def register(self, new_calc, dependencies, always_calc, frequency):
        # TODO: check that dependencies is a list???
        # call super method, now meta can be passed as args or kwargs.
        super(CalcRegistry, self).register(new_calc,
                                          ('dependencies', dependencies),
                                          ('always_calc', always_calc),
                                          ('frequency', frequency))


def index_registry(args, arg_key, reg, ts, idx=None):
    """
    Index into a :class:`~circus.core.Registry` to return arguments
    from :class:`~circus.core.data_sources.DataRegistry` and
    :class:`~circus.core.outputs.OutputRegistry` based on the
    calculation parameter file.

    :param args: Arguments field from the calculation parameter file.
    :param arg_key: Either "data" or "output".
    :type arg_key: str
    :param reg: Registry in which to index to get the arguments.
    :type reg: :class:`~circus.core.Registry`
    :param ts: Timestep [units of time].
    :param idx: [None] Index of current timestep for dynamic calculations.

    Required arguments for static and dynamic calculations are specified in the
    calculation parameter file by the "args" key. Arguments can be from
    either the data registry or the outputs registry, which is denoted by the
    "data" and "output" keys. Each argument is a dictionary whose key is the
    name of the argument in the formula specified and whose value can be one of
    the following:

    * The name of the argument in the registry ::

        {"args": {"output": {"T_bypass": "T_bypass_diode"}}}

      maps the formula argument "T_bypass" to the output registry item
      "T_bypass_diode".

    * A list with the name of the argument in the registry as the first element
      and a negative integer denoting the index relative to the current
      timestep as the second element ::

        {"args": {"data": {"T_cell": ["Tcell", -1]}}}

      indexes the previous timestep of "Tcell" from the data registry.

    * A list with the name of the argument in the registry as the first element
      and a list of positive integers denoting the index into the item from the
      registry as the second element ::

        {"args": {"data": {"cov": ["bypass_diode_covariance", [2]]}}}

      indexes the third element of "bypass_diode_covariance".

    * A list with the name of the argument in the registry as the first
      element, a negative real number denoting the time relative to the current
      timestep as the second element, and the units of the time as the third ::

        {"args": {"data": {"T_cell": ["Tcell", -1, 'day']}}}

      indexes the entire previous day of "Tcell".
    """
    # iterate over "data"/"output" arguments
    _args = args.get(arg_key, {})
    args = dict.fromkeys(_args)  # make dictionary from arguments
    # TODO: move this to new Registry method or __getitem__
    # TODO: replace idx with datetime object and use timeseries to interpolate
    # into data, not necessary for output since that will conform to idx
    for k, v in _args.iteritems():
        # switch based on string type instead of sequence
        if isinstance(v, basestring):
            # the default assumes the current index
            args[k] = reg[v] if reg.isconstant[v] else reg[v][idx]
        elif len(v) < 3:
            if reg.isconstant[v[0]]:
                # only get indices specified by v[1]
                # tuples interpreted as a list of indices, see
                # NumPy basic indexing: Dealing with variable
                # numbers of indices within programs
                args[k] = reg[v[0]][tuple(v[1])]
            elif v[1] < 0:
                # specified offset from current index
                args[k] = reg[v[0]][idx + v[1]]
            else:
                # get indices specified by v[1] at current index
                args[k] = reg[v[0]][idx][tuple(v[1])]
        else:
            # specified timedelta from current index
            # FIXME: dt is hardcoded here, but it could be called anything, if
            # this is **THE** name, then put it in core
            dt = 1 + (v[1] * UREG[str(v[2])] / ts).simplified.item()
            # TODO: deal with fractions of timestep
            args[k] = reg[v[0]][(idx + dt):(idx + 1)]
    return args


# TODO: change me to Calculation
class Calc(object):
    """
    A class for all calculations.

    :param param_file: Filename of parameter file for reading calculation.
    :type param_file: str
    """
    def __init__(self, param_file):
        #: parameter file
        self.param_file = param_file
        # read and load JSON parameter map file as "parameters"
        with open(param_file, 'r') as fp:
            #: parameters from file for reading calculation
            self.parameters = json.load(fp)
        #: ``True`` if always calculated (day and night)
        self.always_calc = self.parameters.get('always_calc', False)
        freq = self.parameters.get('frequency', [1, ''])
        #: frequency calculation is calculated in intervals or units of time
        self.frequency = freq[0] * UREG[str(freq[1])]
        #: list of dependencies
        self.dependencies = self.parameters.get('dependencies', [])
        #: list of static calculations
        self.static = self.parameters.get('static', [])
        #: list of dynamic calculations
        self.dynamic = self.parameters.get('dynamic', [])

    # TODO: move calculators to Calculator class, pass as arg to Calculation
    def calc_static(self, formula_reg, data_reg, out_reg):
        """
        A static explicit marching calculator.

        :param formula_reg: Registry of formulas.
        :type formula_reg: :class:`~circus.core.Registry`
        :param data_reg: Data registry.
        :type data_reg: \
            :class:`~circus.core.data_sources.DataRegistry`
        :param out_reg: Outputs registry.
        :type out_reg: :class:`~circus.core.Registry`
        """
        # override this calculator in subclasses if this calculator doesn't do
        # the trick. EG: if you need to use a solver
        # TODO: move calculators to separate class and add calculator as arg in
        # constructor
        timestep = data_reg['dt']  # timestep
        if self.static:
            # loop over static calcs
            for calc in self.static:
                # get the formula-key from each static calc
                formula = formula_reg[calc['formula']]
                args = calc['args']
                data = index_registry(args, 'data', data_reg, timestep)
                output = index_registry(args, 'output', out_reg, timestep)
                kwargs = dict(data, **output)
                returns = calc['returns']  # return arguments
                retval = formula(**kwargs)
                if len(returns) > 1:
                    # more than one return, zip them up
                    out_reg.update(zip(returns, retval))
                else:
                    # only one return, get it by index at 0
                    out_reg[returns[0]] = retval

    # TODO: refactor to remove redundant code!
    def calc_dynamic(self, idx, formula_reg, data_reg, out_reg):
        """
        A dynamic explicit marching calculator.

        :param idx: Interval index.
        :type idx: int
        :param formula_reg: Registry of formulas.
        :type formula_reg: :class:`~circus.core.Registry`
        :param data_reg: Data registry.
        :type data_reg: \
            :class:`~circus.core.data_sources.DataRegistry`
        :param out_reg: Outputs registry.
        :type out_reg: :class:`~circus.core.Registry`
        """
        # override this calculator in subclasses if this calculator doesn't do
        # the trick. EG: if you need to use a solver
        # TODO: move calculators to separate class and add calculator as arg in
        # constructor
        timestep = data_reg['dt']  # timestep
        # TODO: maybe add ``start_at`` parameter combined with ``frequency``
        # Determine if calculation is scheduled for this timestep
        if (self.frequency.dimensionality ==
            UREG['dimensionless'].dimensionality):
            # Frequency with units of # of intervals
            idx_tot = (out_reg['t_tot'][idx] / data_reg['dt']).simplified
            is_scheduled = (idx_tot % self.frequency) == 0
        else:
            # Frequency with units of time
            is_scheduled = (out_reg['t_tot'][idx] % self.frequency) == 0
        if self.dynamic and is_scheduled:
            for calc in self.dynamic:
                formula = formula_reg[calc['formula']]
                args = calc['args']
                data = index_registry(args, 'data', data_reg, timestep, idx)
                output = index_registry(args, 'output', out_reg, timestep, idx)
                kwargs = dict(data, **output)
                returns = calc['returns']  # return arguments
                retval = formula(**kwargs)
                if len(returns) > 1:
                    # more than one return, zip them up
                    for k, v in zip(returns, retval):
                        out_reg[k][idx] = v
                else:
                    # only one return, get it by index at 0
                    out_reg[returns[0]][idx] = retval


class MetaUserCalculation(type):
    def __new__(cls, name, bases, attr):
        bases = tuple([b for b in bases if not b in Calc.__bases__])
        if Calc not in bases:
            bases += (Calc,)  # add Calc to bases
        param_file = os.path.join(attr['calcs_path'], attr['calcs_file'])

        def __init__(self):
            Calc.__init__(self, param_file)

        attr['__init__'] = __init__  # add `__init__` attribute to class
        return super(MetaUserCalculation, cls).__new__(cls, name, bases, attr)


class MetaCalculation(MetaUserCalculation):
    def __new__(cls, name, bases, attr):
        attr['calcs_path'] = _CALCS
        return super(MetaCalculation, cls).__new__(cls, name, bases, attr)
