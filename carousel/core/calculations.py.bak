# -*- coding: utf-8 -*-

"""
This module provides base classes for calculations. All calculations should
inherit from one of the calcs in this module.
"""

from carousel.core import logging, CommonBase, Registry, UREG, Parameter
from carousel.core.calculators import Calculator

LOGGER = logging.getLogger(__name__)


class CalcParameter(Parameter):
    """
    Fields for calculations.
    """
    _attrs = ['dependencies', 'always_calc', 'frequency', 'formula', 'args',
              'returns', 'calculator', 'is_dynamic']


class CalcRegistry(Registry):
    """
    A registry for calculations. Each key is a calculation. The value
    of each calculation is split into 2 dictionaries: "static" and
    "dynamic". Static calculations occur once at the beginning of a simulation
    and dynamic calculations occur at every interval. The contents of either
    the "static" or "dynamic" key is an ordered list of formulas, their
    arguments and return values.

    Calculations can list `dependencies <http://xkcd.com/754/>`_ that must be
    calculated first. Calculations marked as `always_calc` will not be limited
    by thresholds set in simulations. The frequency determines how often to
    dynamic calculations occur. Frequency can be given in intervals or can list
    a quantity of time, _EG:_ ``2 * UREG.hours``.
    """
    #: meta names
    meta_names = ['dependencies', 'always_calc', 'frequency', 'calculator',
                  'is_dynamic', 'calc_source']

    def register(self, new_calc, *args, **kwargs):
        """
        Register calculations and meta data.

        * ``dependencies`` - list of prerequisite calculations
        * ``always_calc`` - ``True`` if calculation ignores thresholds
        * ``frequency`` - frequency of calculation in intervals or units of time

        :param new_calc: register new calculation
        """
        kwargs.update(zip(self.meta_names, args))
        # dependencies should be a list of other calculations
        if isinstance(kwargs['dependencies'], basestring):
            kwargs['dependencies'] = [kwargs['dependencies']]
        # call super method, now meta can be passed as args or kwargs.
        super(CalcRegistry, self).register(new_calc, **kwargs)


class CalcBase(CommonBase):
    """
    Base calculation meta class.
    """
    _path_attr = 'calcs_path'
    _file_attr = 'calcs_file'
    _param_cls = CalcParameter

    def __new__(mcs, name, bases, attr):
        # use only with Calc subclasses
        if not CommonBase.get_parents(bases, CalcBase):
            return super(CalcBase, mcs).__new__(mcs, name, bases, attr)
        # set _meta combined from bases
        attr = mcs.set_meta(bases, attr)
        # set param file full path if calculations path and file specified or
        # try to set parameters from class attributes except private/magic
        attr = mcs.set_param_file_or_parameters(attr)
        return super(CalcBase, mcs).__new__(mcs, name, bases, attr)


class Calc(object):
    """
    A class for all calculations.
    """
    __metaclass__ = CalcBase

    def __init__(self):
        meta = getattr(self, CalcBase._meta_attr)
        parameters = getattr(self, CalcBase._param_attr)
        #: ``True`` if always calculated (day and night)
        self.always_calc = dict.fromkeys(
            parameters, getattr(meta, 'always_calc', False)
        )
        freq = getattr(meta, 'frequency', [1, ''])
        #: frequency calculation is calculated in intervals or units of time
        self.frequency = dict.fromkeys(parameters, freq[0] * UREG(str(freq[1])))
        #: dependencies
        self.dependencies = dict.fromkeys(
            parameters, getattr(meta, 'dependencies', [])
        )
        #: name of :class:`Calc` superclass
        self.calc_source = dict.fromkeys(parameters, self.__class__.__name__)
        #: calculator
        self.calculator = dict.fromkeys(
            parameters, getattr(meta, 'calculator', Calculator)
        )
        #: ``True`` if calculations are dynamic, ``False`` if static
        self.is_dynamic = dict.fromkeys(
            parameters, getattr(meta, 'is_dynamic', False)
        )
        #: calculations
        self.calcs = {}
        for k, v in parameters.iteritems():
            self.calcs[k] = {
                key: v[key] for key in ('formula', 'args', 'returns')
            }
            keys = ('dependencies', 'always_calc', 'frequency', 'calculator',
                    'is_dynamic')
            for key in keys:
                value = v.get(key)
                if value is not None:
                    getattr(self, key)[k] = value
