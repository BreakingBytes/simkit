# -*- coding: utf-8 -*-

"""
This module contains formulas for calculating PV power.
"""

import pvlib
from flying_circus.core import UREG


@UREG.wraps(('W', ), (None, 'V', 'W'))
def f_ac_power(inverter, v_mp, p_mp):
    """
    Calculate AC power

    :param inverter:
    :param v_mp:
    :param p_mp:
    :return: AC power [W]
    """
    return pvlib.pvsystem.snlinverter(inverter, v_mp, p_mp)


@UREG.wraps(('A', 'A', 'V', 'V', 'W', 'dimensionless'),
            (None, 'W/m**2', 'W/m**2', 'degC', 'dimensionless', 'deg'))
def f_dc_power(module, poa_direct, poa_diffuse, cell_temp, am_abs, aoi):
    """
    Calculate DC power

    :param module: PV module dictionary or pandas data frame
    :param poa_direct: plane of array direct irradiance [W/m**2]
    :param poa_diffuse: plane of array diffuse irradiance [W/m**2]
    :param cell_temp: PV cell temperature [degC]
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


@UREG.wraps(('degC', ), ('W/m**2', 'm/s', 'degC'))
def f_cell_temp(poa_global, wind_speed, air_temp):
    """
    Calculate cell temperature.

    :param poa_global: plane of array global irradiance [W/m**2]
    :param wind_speed: wind speed [m/s]
    :param air_temp: ambient dry bulb air temperature [degC]
    :return: cell temperature [degC]
    """
    return pvlib.pvsystem.sapm_celltemp(poa_global, wind_speed, air_temp)


@UREG.wraps(('deg', ), ('deg', 'deg', 'deg', 'deg'))
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
