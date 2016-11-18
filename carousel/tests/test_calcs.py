"""
test calculations
"""

from nose.tools import ok_, eq_
from carousel.core.calculations import Calc, CalcParameter
from carousel.tests import PROJ_PATH, sandia_performance_model
import os
import uncertainties
from pvlib.solarposition import get_solarposition as solpos
import logging
import numpy as np

LOGGER = logging.getLogger(__name__)


def test_calc_metaclass():
    """
    Test calculation class is created with params file using metaclass
    """

    class CalcTest1(Calc):
        class Meta:
            calcs_file = 'utils.json'
            calcs_path = os.path.join(PROJ_PATH, 'calculations')

    calc_test1 = CalcTest1()
    ok_(isinstance(calc_test1, Calc))
    eq_(calc_test1.param_file,
        os.path.join(PROJ_PATH, 'calculations', 'utils.json'))

    class CalcTest2(Calc):
        energy = CalcParameter(
            calculator="static",
            dependencies=["ac_power", "daterange"],
            formula="f_energy",
            args={"outputs": {"ac_power": "Pac", "times": "timestamps"}},
            returns=["hourly_energy", "hourly_timeseries"]
        )
        monthly_rollup = CalcParameter(
            calculator="static",
            dependencies=["energy"],
            formula="f_rollup",
            args={
                "data": {"freq": "MONTHLY"},
                "outputs": {"items": "hourly_energy",
                            "times": "hourly_timeseries"}
            },
            returns=["monthly_energy"]
        )
        yearly_rollup = CalcParameter(
            calculator="static",
            dependencies=["energy"],
            formula="f_rollup",
            args={"data": {"freq": "YEARLY"},
                  "outputs": {"items": "hourly_energy",
                              "times": "hourly_timeseries"}},
            returns=["annual_energy"]
        )

    calc_test2 = CalcTest2()
    ok_(isinstance(calc_test2, Calc))
    for k, v in calc_test1.parameters.iteritems():
        eq_(calc_test2.parameters[k], v)


def test_static_calc_unc():
    """
    Test uncertainty propagation in static calculations using Uncertainties.
    """

    # FIXME: this shouldn't have to run a model to test the uncertainty
    test_model_file = os.path.join(PROJ_PATH, 'models',
                                   'sandia_performance_model-Tuscon.json')
    test_model = sandia_performance_model.SAPM(test_model_file)  # create model
    test_model.command('start')  # start simulation
    # get parameters from model
    dt = test_model.outputs.reg['timestamps']  # timestamps
    latitude = test_model.data.reg['latitude'].m  # latitude [degrees]
    longitude = test_model.data.reg['longitude'].m  # longitude [degrees]
    zenith = test_model.outputs.reg['solar_zenith'].m  # zenith [degrees]
    s_ze_ze = test_model.outputs.reg.variance['solar_zenith']['solar_zenith']
    azimuth = test_model.outputs.reg['solar_azimuth'].m  # azimuth [degrees]
    s_az_az = test_model.outputs.reg.variance['solar_azimuth']['solar_azimuth']
    # get uncertainties percentages in base units
    lat_unc = test_model.data.reg.uncertainty['latitude']['latitude']
    lat_unc = lat_unc.to_base_units().m
    lon_unc = test_model.data.reg.uncertainty['longitude']['longitude']
    lon_unc = lon_unc.to_base_units().m
    # create ufloat Uncertainties from parameters
    lat_unc = uncertainties.ufloat(latitude, np.abs(latitude * lat_unc))
    lon_unc = uncertainties.ufloat(longitude, np.abs(longitude * lon_unc))
    test_unc = []  # empty list to collect return values
    for n in xrange(96):
        # Uncertainties wrapped functions must return only scalar float
        f_ze_unc = uncertainties.wrap(
            lambda lat, lon: solpos(dt[n], lat, lon)['apparent_zenith'].item()
        )
        f_az_unc = uncertainties.wrap(
            lambda lat, lon: solpos(dt[n], lat, lon)['azimuth'].item()
        )
        ze_unc, az_unc = f_ze_unc(lat_unc, lon_unc), f_az_unc(lat_unc, lon_unc)
        LOGGER.debug(
            '%s: ze = %g +/- %g%%, az = %g +/- %g%%', dt[n].isoformat(),
            zenith[n], np.sqrt(s_ze_ze[n]) * 100,
            azimuth[n], np.sqrt(s_az_az[n]) * 100
        )
        LOGGER.debug(
            'Uncertainties test %2d: ze = %g +/- %g%%, az = %g +/- %g%%', n,
            ze_unc.n, ze_unc.s / ze_unc.n * 100,
            az_unc.n, az_unc.s / az_unc.n * 100
        )
        assert np.isclose(zenith[n], ze_unc.n)
        assert np.isclose(np.sqrt(s_ze_ze[n]), ze_unc.s / ze_unc.n)
        assert np.isclose(azimuth[n], az_unc.n)
        assert np.isclose(np.sqrt(s_az_az[n]), az_unc.s / az_unc.n)
        test_unc.append({'ze': ze_unc, 'az': az_unc})
    return test_model, test_unc


if __name__ == '__main__':
    tm, tu = test_static_calc_unc()
    test_calc_metaclass()