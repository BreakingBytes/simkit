.. _tutorial-3:

Tutorial 3: Formulas
====================
In the :ref:`last tutorial <tutorial-2>` we created a calculation that used data
and outputs as arguments in formulas that resulted in new output values. In this
tutorial we'll create the formulas that are used in calculations.

Formulas
--------
Formulas are functions or equations that take input arguments and return values.
Carousel currently supports formulas that are written in Python as function
definitions or strings that can be evaluated by the Python
`numexpr <https://pypi.python.org/pypi/numexpr>`_ package. It's convenient to
group related formulas together in the same module or file. To add the formulas
we need for this example create a Python module in our project formulas folder
called ``utils.py`` and copy the following code. ::

    # -*- coding: utf-8 -*-

    """
    This module contains formulas for calculating PV power.
    """

    import numpy as np
    from scipy import constants as sc_const
    import itertools
    from dateutil import rrule


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
        :param times: times corresponding to items
        :param freq: One of the ``dateutil.rrule`` frequency constants
        :type freq: str
        :param wkst: One of the ``dateutil.rrule`` weekday constants
        :type wkst: str
        :return: generator
        """
        timeseries = zip(times, items)  # timeseries map of items
        # create a key lambda to group timeseries by
        if freq.upper() == 'DAILY':
            def key(ts_): return ts_[0].day
        elif freq.upper() == 'WEEKLY':
            weekday = getattr(rrule, wkst.upper())  # weekday start
            # generator that searches times for weekday start
            days = (day for day in times if day.weekday() == weekday.weekday)
            day0 = days.next()  # first weekday start of all times

            def key(ts_): return (ts_[0] - day0).days // 7
        else:
            def key(ts_): return getattr(ts_[0], freq.lower()[:-2])
        for k, ts in itertools.groupby(timeseries, key):
            yield k, ts


    def f_rollup(items, times, freq):
        """
        Use :func:`groupby_freq` to rollup items

        :param items: items in timeseries
        :param times: times corresponding to items
        :param freq: One of the ``dateutil.rrule`` frequency constants
        :type freq: str
        """
        rollup = [np.sum(item for __, item in ts)
                  for _, ts in groupby_freq(items, times, freq)]
        return np.array(rollup)

Formulas can use any code or packages necessary. However here are a couple of
conventions that may be helpful.

* keep formulas short
* name formulas after the main output preceeded by ``f_`` - Carousel can be
  configured to search for functions with this prefix
* use NumPy arrays for arguments so uncertainty and units are propagated
* document functons verbosely

Formula Class
-------------
We'll use the same ``performance.py`` module again that we used in the previous
tutorials to add these formulas to our model. We'll need to import the
:class:`carousel.core.formulas.Formula` class into our model. Then we'll list
the formulas and attributes that tell Carousel how to use them.


    from carousel.core.formulas import Formula


    class UtilityFormulas(Formula):
        """
        Formulas for PV Power demo
        """
        module = ".utils"
        package = "formulas"
        formulas = {
            "f_energy": {
                "args": ["ac_power", "times"],
                "units": [["watt_hour", None], ["W", None]]
            },
            "f_rollup": {
                "args": ["items", "times", "freq"],
                "units": ["=A", ["=A", None, None]]
            }
        }

