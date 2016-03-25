# -*- coding: utf-8 -*-

"""
This module contains formulas for calculating PV power.
"""

import pvlib
import numpy as np
from datetime import datetime
import pandas as pd
from circus.core import UREG
import itertools
from dateutil import rrule


def f_daterange(freq, *args, **kwargs):
    """
    Use ``dateutil.rrule`` to create a range of dates. The frequency must be a
    string in the following list: YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY,
    MINUTELY, or SECONDLY.

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
    freq = getattr(rrule, freq, 'HOURLY')
    return list(rrule.rrule(freq, *args, **kwargs))


def f_energy(Pac, timeseries):
    """
    Calculate the total energy accumulated from AC power at the end of each
    timestep between the given timeseries.

    :param Pac: AC Power [W]
    :param timeseries: times
    :type timeseries: np.datetime64[s]
    :return: energy [W*h] and energy times
    """
    dt = np.diff(timeseries)  # calculate timesteps
    # convert timedeltas to quantities
    dt = dt.astype('timedelta64[s]').astype('float') * UREG['s']
    energy = dt * (Pac[:-1] + Pac[1:]) / 2  # energy accumulate during timestep
    energy = energy.rescale('W*h')  # rescale to
    return energy, timeseries[1:]


#iterator
tslist = (pytz.UTC.localize(t).astimezone(PST) for t in ts.tolist())
key = lambda x: x.month
def get_groups(tslist, key):
    for k, g in itertools.groupby(tslist, key):
        yield k, g



def group_by(items, timeseries, intervals):

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


def f_rollup(integrand, timeseries, intervals=None):
    """
    Rollup integrand by intervals

    :param integrand:
    :param interval:
    :return:
    """
    np.trapz(integrand, x=timeseries.astype('float')*pq.s).rescale(ureg['W*h'])
    return
    # pandas just works if timesteps are uniform
    # might have to adjust to hours if ts
    # integrand = pd.DataFrame(integrand, index=timeseries)
    # integrand.resample(intervals).sum()[0].tolist()
