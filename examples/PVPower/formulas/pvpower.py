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
    :returns: AC power [kW]
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
    :returns: short circuit current (Isc) [A], max. power current (Imp) [A],
        open circuit voltage (Voc) [V], max. power voltage (Vmp) [V],
        max. power (Pmp) [W], effective irradiance (Ee) [suns]
    """
    dc = pvlib.pvsystem.sapm(
        module, poa_direct, poa_diffuse, cell_temp, am_abs, aoi
    )
    return dc['i_sc'], dc['i_mp'], dc['v_oc'], dc['v_mp'], dc['p_mp'], dc['Ee']


def f_celltemp(poa_global, wind_speed, air_temp):
    """
    Calculate cell temperature.

    :param poa_global: plane of array global irradiance [W/m**2]
    :param wind_speed: wind speed [m/s]
    :param air_temp: ambient dry bulb air temperature [C]
    :return: cell temperature [C]
    """
    temps = pvlib.pvsystem.sapm_celltemp(
        poa_global, wind_speed, air_temp
    )
    return temps
