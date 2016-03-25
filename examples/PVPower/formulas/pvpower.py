# -*- coding: utf-8 -*-

"""
This module contains formulas for calculating PV power.
"""

import numpy as np
from datetime import datetime
from circus.core import UREG
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
    return rrule.rrule(freq, *args, **kwargs)


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
    dt = dt.astype('timedelta64[s]').astype('float') * UREG['s']
    # energy accumulate during timestep
    energy = dt * (ac_power[:-1] + ac_power[1:]) / 2
    energy = energy.rescale('W*h')  # rescale to W*h
    return energy, times[1:]


def groupby_freq(items, times, freq, wkst=6):
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



# def group_by(items, timeseries, intervals):

    # #method 0
    # months = []
    # month = []
    # tslist = (pytz.UTC.localize(t).astimezone(pst) for t in ts.tolist())
    # for k, g in itertools.groupby(tslist, lambda x: x.month):
    #     months.append(list(g))
    #     month.append(k)
    # # method 1
    # output = [[] for _ in xrange(intervals)]
    # for item, t  in zip(items, timeseries):
    #     output[t.item().month - 1].append(item)
    # # method 2
    # df = pd.DataFrame(items, index=timeseries)
    # output = [_ for _ in df.groupby(df.index.month)]


# def f_rollup(items, times, key):
#     """
#     Rollup integrand by intervals
#
#     :param items:
#     :param times:
#     :param key:
#     :return:
#     """
#
#     if key
#     for k, g in itertools.groupby(timeseries, key):
#
#     np.trapz(integrand, x=timeseries.astype('float')*pq.s).rescale(ureg['W*h'])
#     return
#     # pandas just works if timesteps are uniform
#     # might have to adjust to hours if ts
#     # integrand = pd.DataFrame(integrand, index=timeseries)
#     # integrand.resample(intervals).sum()[0].tolist()
