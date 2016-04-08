# -*- coding: utf-8 -*-

"""
This module contains formulas for calculating PV power.
"""

import pvlib
from circus.core import UREG


@UREG.wraps(('W/m**2', 'W/m**2', 'W/m**2'),
            ('deg', 'deg', 'deg', 'deg', 'W/m**2', 'W/m**2', 'W/m**2', 'W/m**2',
             'dimensionless', None))
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
