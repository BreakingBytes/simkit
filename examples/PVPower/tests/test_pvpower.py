"""
Tests for pvpower formulas
"""

from datetime import datetime, timedelta
import numpy as np
import pytz
from time import clock
import logging
# XXX: add circus to python path for testing!
from circus.core import UREG
# XXX: add pvpower to python path for testing!
from pvpower.formulas import PVPowerFormulas

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
PST = pytz.timezone('US/Pacific')
FORMULAS = PVPowerFormulas()


MONTHLY_ENERGY = [186000.0, 168000.0, 186000.0, 180000.0, 186000.0, 180000.0,
                  186000.0, 186000.0, 180000.0, 186000.0, 180000.0, 186000.0]


def test_rollup():
    """
    test rollup
    """
    dtstart = PST.localize(datetime(2007, 1, 1, 0, 0, 0))
    dates = FORMULAS['f_daterange']('HOURLY', dtstart=dtstart, count=8761)
    assert dates[0] == dtstart
    assert dates[12] == dtstart + timedelta(hours=12)
    ac_power = 1000. * np.sin(np.arange(12) * np.pi / 12.0) ** 2
    ac_power = np.pad(ac_power, [6, 6], 'constant')
    ac_power = np.append(np.tile(ac_power, (365,)), [0]) * UREG.watt
    energy, energy_times = FORMULAS['f_energy'](ac_power, dates)
    assert energy.units == UREG.Wh
    start = clock()
    monthly_energy = FORMULAS['f_rollup'](energy, energy_times, 'MONTHLY')
    stop = clock()
    LOGGER.debug('elapsed time: %g [ms]', (stop - start) * 1000.)
    assert np.allclose(monthly_energy[:12], MONTHLY_ENERGY)
    return dates, ac_power, energy, energy_times, monthly_energy


if __name__ == "__main__":
    results = test_rollup()
