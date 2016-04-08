"""
tests for pvpower formulas
"""

from datetime import datetime
import numpy as np
import quantities as pq
import pytz
import imp
import os
from time import clock
import logging
from circus.core import UREG

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
PST = pytz.timezone('US/Pacific')
MODNAME = 'pvpower'
BASEDIR = os.path.dirname(__file__)
LOGGER.debug('base dir:\n> %s', BASEDIR)
MODPATH = os.path.abspath(os.path.join(BASEDIR, '..', 'formulas'))
LOGGER.debug('path:\n> %s', MODPATH)
MODFID, MODFN, MODINFO = None, None, None

try:
    MODFID, MODFN, MODINFO = imp.find_module(MODNAME,[MODPATH])
    MOD = imp.load_module(MODNAME, MODFID, MODFN, MODINFO)
finally:
    if MODFID:
        MODFID.close()


def test_rollup():
    """
    test rollup
    """
    dtstart = PST.localize(datetime(2007, 1, 1, 0, 0, 0))
    dates = MOD.f_daterange('HOURLY', dtstart=dtstart, count=8761)
    Pac = 1000. * np.sin(np.arange(24) / np.pi)
    Pac = np.append(np.tile(Pac, 365), 0) * UREG.watt
    energy, energy_times = MOD.f_energy(Pac, dates)

    # test using Pint wrapper
    LOGGER.debug('Pint wrapper')
    c = clock()
    MOD.f_rollup(energy, energy_times, 'MONTHLY')
    LOGGER.debug('elapsed time: %g [ms]', (clock() - c) * 1000.)

    # just test using Quantities
    energy_pq = energy.magnitude * pq.watt * pq.hour
    LOGGER.debug('Quantities only')
    c = clock()
    MOD.f_rollup_pq(energy_pq, energy_times, 'MONTHLY')
    LOGGER.debug('elapsed time: %g [ms]', (clock() - c) * 1000.)

    # just using magnitude with Pint
    LOGGER.debug('magnitude with Pint')
    c = clock()
    MOD.f_rollup_alt(energy, energy_times, 'MONTHLY')
    LOGGER.debug('elapsed time: %g [ms]', (clock() - c) * 1000.)

    # just using magnitude with Quantities
    LOGGER.debug('magnitude with Quantities')
    c = clock()
    MOD.f_rollup_alt(energy_pq, energy_times, 'MONTHLY')
    LOGGER.debug('elapsed time: %g [ms]', (clock() - c) * 1000.)


if __name__ == "__main__":
    test_rollup()
