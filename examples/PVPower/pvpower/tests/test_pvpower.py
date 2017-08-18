"""
Tests for pvpower formulas
"""

from datetime import datetime, timedelta
import numpy as np
import pytz
from carousel.core import UREG, logging, models
from pvpower.sandia_performance_model import (
    UtilityFormulas, IrradianceFormulas
)
from pvpower import sandia_performance_model, sandia_perfmod_newstyle
from pvpower.tests import MODEL_PATH
import os

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
TZ = 'US/Pacific'
PST = pytz.timezone(TZ)
UTIL_FORMULAS = UtilityFormulas()
IRRAD_FORMULAS = IrradianceFormulas()
DTSTART = datetime(2007, 1, 1, 0, 0, 0)
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
OLD_MODEL = os.path.join(MODEL_PATH, 'sandia_performance_model-Tuscon.json')
ANNUAL_ENERGY = np.array(479083.75869040738)


def test_daterange():
    """
    Test date range.
    """
    test_range = 12
    dates = UTIL_FORMULAS['f_daterange'](
        'HOURLY', TZ, dtstart=DTSTART, count=test_range
    )
    dtstart_local = PST.localize(DTSTART)
    for hour in range(test_range):
        assert dates[hour] == dtstart_local + timedelta(hours=hour)
        assert dates[hour].tzinfo.zone == TZ
    return dates


def test_solarposition():
    """
    Test solar position algorithm.
    """
    lat, lon = 38.0 * UREG.degrees, -122.0 * UREG.degrees
    times = UTIL_FORMULAS['f_daterange'](
        'HOURLY', TZ, dtstart=(DTSTART + timedelta(hours=8)), count=9
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


def test_new_style():
    """
    Test new style Carousel model.
    """
    m = sandia_perfmod_newstyle.NewSAPM()
    assert isinstance(m, models.Model)
    m.command('start')
    annual_energy = np.sum(m.registries['outputs']['annual_energy'].m)
    assert np.isclose(annual_energy, ANNUAL_ENERGY)
    return m


def test_old_style():
    """
    Test old style Carousel model.
    """
    m = sandia_performance_model.SAPM(OLD_MODEL)
    assert isinstance(m, models.Model)
    m.command('start')
    annual_energy = np.sum(m.registries['outputs']['annual_energy'].m)
    assert np.isclose(annual_energy, ANNUAL_ENERGY)
    return m


if __name__ == "__main__":
    results = test_rollup()
    m_old = test_old_style()
    m_new = test_new_style()
