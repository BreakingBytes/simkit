# -*- coding: utf-8 -*-

"""
This module contains formulas for calculating PV power.
"""

import pvlib


def f_ac_power(inverter, v_mp, p_mp):
    """
    Calculate AC power

    :param inverter:
    :param v_mp:
    :param p_mp:
    :return: AC power [W]
    """
    return pvlib.pvsystem.snlinverter(v_mp, p_mp, inverter).flatten()


def f_dc_power(effective_irradiance, cell_temp, module):
    """
    Calculate DC power using Sandia Performance model

    :param effective_irradiance: effective irradiance [suns]
    :param cell_temp: PV cell temperature [degC]
    :param module: PV module dictionary or pandas data frame
    :returns: i_sc, i_mp, v_oc, v_mp, p_mp
    """
    dc = pvlib.pvsystem.sapm(effective_irradiance, cell_temp, module)
    fields = ('i_sc', 'i_mp', 'v_oc', 'v_mp', 'p_mp')
    return tuple(dc[field] for field in fields)


def f_effective_irradiance(poa_direct, poa_diffuse, am_abs, aoi, module):
    """
    Calculate effective irradiance for Sandia Performance model

    :param poa_direct: plane of array direct irradiance [W/m**2]
    :param poa_diffuse: plane of array diffuse irradiance [W/m**2]
    :param am_abs: absolute air mass [dimensionless]
    :param aoi: angle of incidence [degrees]
    :param module: PV module dictionary or pandas data frame
    :return: effective irradiance (Ee) [suns]
    """
    Ee = pvlib.pvsystem.sapm_effective_irradiance(poa_direct, poa_diffuse,
                                                  am_abs, aoi, module)
    return Ee.reshape(1, -1)


def f_cell_temp(poa_global, wind_speed, air_temp):
    """
    Calculate cell temperature.

    :param poa_global: plane of array global irradiance [W/m**2]
    :param wind_speed: wind speed [m/s]
    :param air_temp: ambient dry bulb air temperature [degC]
    :return: cell temperature [degC]
    """
    temps = pvlib.pvsystem.sapm_celltemp(poa_global, wind_speed, air_temp)
    return temps['temp_cell'].values, temps['temp_module'].values


def f_aoi(surface_tilt, surface_azimuth, solar_zenith, solar_azimuth):
    """
    Calculate angle of incidence

    :param surface_tilt:
    :param surface_azimuth:
    :param solar_zenith:
    :param solar_azimuth:
    :return: angle of incidence [deg]
    """
    return pvlib.irradiance.aoi(surface_tilt, surface_azimuth,
                                solar_zenith, solar_azimuth)
