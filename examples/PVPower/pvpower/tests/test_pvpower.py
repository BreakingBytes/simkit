"""
Tests for pvpower formulas
"""

from datetime import datetime, timedelta
import numpy as np
import pytz
from carousel.core import UREG, logging
from pvpower.sandia_performance_model import (
    UtilityFormulas, IrradianceFormulas
)
from pvpower import sandia_performance_model
from pvpower.tests import MODEL_PATH
import os

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
PST = pytz.timezone('US/Pacific')
UTIL_FORMULAS = UtilityFormulas()
IRRAD_FORMULAS = IrradianceFormulas()
DTSTART = PST.localize(datetime(2007, 1, 1, 0, 0, 0))
MONTHLY_ENERGY = [186000.0, 168000.0, 186000.0, 180000.0, 186000.0, 180000.0,
                  186000.0, 186000.0, 180000.0, 186000.0, 180000.0, 186000.0]
ZENITH = [
    84.67227032399542, 75.69700469024768, 68.32442897476993, 63.22974106430276,
    61.01563669117582, 62.00067006350331, 66.0382089666321, 72.60444584135432,
    81.04253480488877
]
AZIMUTH = [
    124.64915808, 135.21222923, 147.46982483, 161.53685504, 176.95197338,
    192.61960738, 207.30533949, 220.27975359, 231.46642409
]


def test_daterange():
    """
    Test date range.
    """
    dates = UTIL_FORMULAS['f_daterange']('HOURLY', dtstart=DTSTART, count=12)
    for hour in xrange(12):
        assert dates[hour] == DTSTART + timedelta(hours=hour)
    return dates


def test_solarposition():
    """
    Test solar position algorithm.
    """
    lat, lon = 38.0 * UREG.degrees, -122.0 * UREG.degrees
    times = UTIL_FORMULAS['f_daterange'](
        'HOURLY', dtstart=(DTSTART + timedelta(hours=8)), count=9
    )
    cov = np.array([[0.0001, 0], [0, 0.0001]])
    solpos = IRRAD_FORMULAS['f_solpos'](times, lat, lon, __covariance__=cov)
    assert len(solpos) == 4
    ze, az, cov, jac = solpos
    assert ze.u == UREG.degree
    assert az.u == UREG.degree
    assert np.allclose(ze.m, ZENITH)
    assert np.allclose(az.m, AZIMUTH)
    return solpos


def test_rollup():
    """
    Test rollup.
    """
    dates = UTIL_FORMULAS['f_daterange']('HOURLY', dtstart=DTSTART, count=8761)
    ac_power = 1000. * np.sin(np.arange(12) * np.pi / 12.0) ** 2
    ac_power = np.pad(ac_power, [6, 6], 'constant')
    ac_power = np.append(np.tile(ac_power, (365,)), [0]) * UREG.watt
    energy, energy_times = UTIL_FORMULAS['f_energy'](ac_power, dates)
    assert energy.units == UREG.Wh
    monthly_energy = UTIL_FORMULAS['f_rollup'](energy, energy_times, 'MONTHLY')
    assert np.allclose(monthly_energy[:12], MONTHLY_ENERGY)
    return dates, ac_power, energy, energy_times, monthly_energy


if __name__ == "__main__":
    results = test_rollup()
    spm = sandia_performance_model.SAPM(
        os.path.join(MODEL_PATH, 'sandia_performance_model-Tuscon.json')
    )
    spm.command('start')
