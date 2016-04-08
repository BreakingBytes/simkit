# -*- coding: utf-8 -*-

"""
This module contains formulas for calculating PV power.
"""

import numpy as np
from datetime import datetime
from circus.core import UREG
from scipy import constants as sc_const
import itertools
from dateutil import rrule

def f_daterange(freq, *args, **kwargs):
    """
    Use ``dateutil.rrule`` to create a range of dates. The frequency must be a
    string in the following list: YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY,
    MINUTELY or SECONDLY.

    See `dateutil rrule`_ documentation for more detail.

    .. _dateutil rrule: https://dateutil.readthedocs.org/en/latest/rrule.html

    :param freq: One of the ``dateutil.rrule`` frequencies
    :type freq: str
    :param dtstart: start date
    :type dtstart: datetime
    :param interval: interval between each frequency
    :type interval: int
    :param count: max number of recurrences
    :type count: int
    :param until: end date
    :type until: datetime
    :return: range of dates
    :rtype: list
    """
    freq = getattr(rrule, freq.upper()) # get frequency enumeration from rrule
    return list(rrule.rrule(freq, *args, **kwargs))


@UREG.wraps(('Wh', None), ('W', None))
def f_energy(ac_power, times):
    """
    Calculate the total energy accumulated from AC power at the end of each
    timestep between the given times.

    :param ac_power: AC Power [W]
    :param times: times
    :type times: np.datetime64[s]
    :return: energy [W*h] and energy times
    """
    dt = np.diff(times)  # calculate timesteps
    # convert timedeltas to quantities
    dt = dt.astype('timedelta64[s]').astype('float') / sc_const.hour
    # energy accumulate during timestep
    energy = dt * (ac_power[:-1] + ac_power[1:]) / 2
    return energy, times[1:]


def groupby_freq(items, times, freq, wkst='SU'):
    """
    Group timeseries by frequency. The frequency must be a string in the
    following list: YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY or
    SECONDLY. The optional weekstart must be a string in the following list:
    MO, TU, WE, TH, FR, SA and SU.

    :param items: items in timeseries
    :param times:
    :param freq: One of the ``dateutil.rrule`` frequency constants
    :type freq: str
    :param wkst: One of the ``dateutil.rrule`` weekday constants
    :type wkst: str
    :return: generator
    """
    timeseries = zip(times, items)  # timeseries map of items
    # create a key lambda to group timeseries by
    if freq.upper() == 'DAILY':
        key = lambda ts_: ts_[0].day
    elif freq.upper() == 'WEEKLY':
        weekday = getattr(rrule, wkst.upper())  # weekday start
        # generator that searches times for weekday start
        days = (day for day in times if day.weekday() == weekday.weekday)
        day0 = days.next()  # first weekday start of all times
        key = lambda ts_: (ts_[0] - day0).days // 7
    else:
        key = lambda ts_: getattr(ts_[0], freq.lower()[:-2])
    for k, ts in itertools.groupby(timeseries, key):
        yield k, ts


# =======================  =================
# Method                   Benchmark
# =======================  =================
# Pint wrapper             5.25[ms]
# Pint no wrapper          227[ms
# magnitude w/Quantities   55[ms]
# magnitude w/Pint         24[ms]
# Quantities only          675[ms]
# Pint no wrapper w/ unc   2.82[s]


# Pint Wrapper Version (FASTEST)
# pint>=0.7.2
# benchmark 5.28[ms] using test_rollup
# NOTE: without wrap, benchcmark is 227[ms]
# XXX: Pint only!
# Does not work with Quantities b/c it can't apply np.sum or np.array
# stacktrace for np.sum is
# ValueError: Unable to convert between units of "dimensionless" and "h*W"
# np.array, np.concatenate and np.append all strip dimensions from quantities
@UREG.wraps('=A', ('=A', None, None))
def f_rollup(items, times, freq):
    """

    :param items:
    :param times:
    :param freq:
    """
    # This works fine with Pint but it is slow.

    return [np.sum(item for _, item in ts)
            for _, ts in groupby_freq(items, times, freq)]


# magnitude version
# NOTE: since np.append strips dimensions from quantities
# XXX: will not propagate uncertainty
def f_rollup_alt(items, times, freq):
    rollup = [np.sum(item.magnitude for _, item in ts)
              for _, ts in groupby_freq(items, times, freq)]
    return rollup * items.units


# Quantites Slow Version
# XXX: Quantities only
# XXX: will not propagate uncertainty
def f_rollup_pq(items, times, freq):
    rollup = []
    for _, ts in groupby_freq(items, times, freq):
        subtotal = 0 * items.units
        for _, item in ts:
            subtotal += item
        rollup.append(subtotal)
    return rollup * items.units


