"""
tests for pvpower formulas
"""

from datetime import datetime, timedelta
import numpy as np
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

MONTHLY_ENERGY = [186000.0, 168000.0, 186000.0, 180000.0, 186000.0, 180000.0,
                  186000.0, 186000.0, 180000.0, 186000.0, 180000.0, 186000.0]

def test_rollup():
    """
    test rollup
    """
    dtstart = PST.localize(datetime(2007, 1, 1, 0, 0, 0))
    dates = MOD.f_daterange('HOURLY', dtstart=dtstart, count=8761)
    assert dates[0] == dtstart
    assert dates[12] == dtstart + timedelta(hours=12)
    Pac = 1000. * np.sin(np.arange(12) * np.pi / 12.0) ** 2
    Pac = np.pad(Pac, [6, 6], 'constant')
    Pac = np.append(np.tile(Pac, 365), 0) * UREG.watt
    energy, energy_times = MOD.f_energy(Pac, dates)
    assert energy.units == UREG.Wh
    start = clock()
    monthly_energy = MOD.f_rollup(energy, energy_times, 'MONTHLY')
    stop = clock()
    LOGGER.debug('elapsed time: %g [ms]', (stop - start) * 1000.)
    assert np.allclose(monthly_energy[:12], MONTHLY_ENERGY)


if __name__ == "__main__":
    test_rollup()
