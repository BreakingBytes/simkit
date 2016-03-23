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
    :return: AC power [kW]
    """
    return pvlib.pvsystem.snlinverter(inverter, v_mp, p_mp)


def f_dc_power(module, poa_direct, poa_diffuse, cell_temp, am_abs, aoi):
    """
    Calculate DC power

    :param module: PV module dictionary or pandas data frame
    :param poa_direct: plane of array direct irradiance [W/m**2]
    :param poa_diffuse: plane of array diffuse irradiance [W/m**2]
    :param cell_temp: PV cell temperature [C]
    :param am_abs: absolute air mass [dimensionless]
    :param aoi: angle of incidence [degrees]
    :return: short circuit current (Isc) [A], max. power current (Imp) [A],
        open circuit voltage (Voc) [V], max. power voltage (Vmp) [V],
        max. power (Pmp) [W], effective irradiance (Ee) [suns]
    """
    dc = pvlib.pvsystem.sapm(
        module, poa_direct, poa_diffuse, cell_temp, am_abs, aoi
    )
    return dc['i_sc'], dc['i_mp'], dc['v_oc'], dc['v_mp'], dc['p_mp'], dc['Ee']


def f_cell_temp(poa_global, wind_speed, air_temp):
    """
    Calculate cell temperature.

    :param poa_global: plane of array global irradiance [W/m**2]
    :param wind_speed: wind speed [m/s]
    :param air_temp: ambient dry bulb air temperature [C]
    :return: cell temperature [C]
    """
    return pvlib.pvsystem.sapm_celltemp(poa_global, wind_speed, air_temp)


def f_total_irrad(surface_tilt, surface_azimuth, solar_zenith, solar_azimuth,
                  dni, ghi, dhi, extraterrestrial, am_abs, model='perez'):
    """
    Calculate total irradiance

    :param surface_tilt: panel tilt from horizontal [deg]
    :param surface_azimuth: panel azimuth from north [deg]
    :param solar_zenith: refracted solar zenith angle [deg]
    :param solar_azimuth: solar azimuth [deg]
    :param dni: direct normal irradiance [W/m**2]
    :param ghi: global horizonal irradiance [W/m**2]
    :param dhi: diffuse horizontal irradiance [W/m**2]
    :param extraterrestrial: extraterrestrial irradiance [W/m**2]
    :param am_abs: absolute airmass [dimensionless]
    :param model: irradiance model name
    :type model: str
    :return: global, direct and diffuse plane of array irradiance [W/m**2]
    """
    total_irrad = pvlib.irradiance.total_irrad(
        surface_tilt, surface_azimuth, solar_zenith, solar_azimuth, dni, ghi,
        dhi, dni_extra=extraterrestrial, airmass=am_abs, model=model
    )
    poa_global = total_irrad['poa_global']
    poa_direct = total_irrad['poa_direct']
    poa_diffuse = total_irrad['poa_diffuse']
    return poa_global, poa_direct, poa_diffuse


def f_aoi(surface_tilt, surface_azimuth, solar_zenith, solar_azimuth):
    """
    Calculate angle of incidence

    :param surface_tilt:
    :param surface_azimuth:
    :param solar_zenith:
    :param solar_azimuth:
    :return:
    """
    return pvlib.irradiance.aoi(surface_tilt, surface_azimuth,
                                solar_zenith, solar_azimuth)
