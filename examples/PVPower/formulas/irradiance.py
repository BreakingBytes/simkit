# -*- coding: utf-8 -*-

"""
This module contains formulas for calculating PV power.
"""

import pvlib
import pandas as pd


def f_clearsky(times, latitude, longitude, altitude):
    times = pd.DatetimeIndex(times)
    cs = pvlib.clearsky.ineichen(times, latitude, longitude, altitude)
    return cs['dni'].values, cs['ghi'].values, cs['dhi'].values


def f_solpos(times, latitude, longitude):
    times = pd.DatetimeIndex(times)
    solpos = pvlib.solarposition.get_solarposition(times, latitude, longitude)
    return solpos['apparent_zenith'].values, solpos['azimuth'].values


def f_dni_extra(times):
    times = pd.DatetimeIndex(times)
    return pvlib.irradiance.extraradiation(times)


def f_airmass(solar_zenith):
    return pvlib.atmosphere.relativeairmass(solar_zenith)


def f_pressure(altitude):
    return pvlib.atmosphere.alt2pres(altitude)


def f_am_abs(airmass, pressure):
    return pvlib.atmosphere.absoluteairmass(airmass, pressure)


def f_total_irrad(times, surface_tilt, surface_azimuth, solar_zenith,
                  solar_azimuth, dni, ghi, dhi, dni_extra, am_abs,
                  model='haydavies'):
    """
    Calculate total irradiance

    :param times: timestamps
    :param surface_tilt: panel tilt from horizontal [deg]
    :param surface_azimuth: panel azimuth from north [deg]
    :param solar_zenith: refracted solar zenith angle [deg]
    :param solar_azimuth: solar azimuth [deg]
    :param dni: direct normal irradiance [W/m**2]
    :param ghi: global horizonal irradiance [W/m**2]
    :param dhi: diffuse horizontal irradiance [W/m**2]
    :param dni_extra: extraterrestrial irradiance [W/m**2]
    :param am_abs: absolute airmass [dimensionless]
    :param model: irradiance model name, default is ``'haydavies'``
    :type model: str
    :return: global, direct and diffuse plane of array irradiance [W/m**2]
    """
    # make a DataFrame for time series arguments
    df = pd.DataFrame(
        {'solar_zenith': solar_zenith, 'solar_azimuth': solar_azimuth,
         'dni': dni, 'ghi': ghi, 'dhi': dhi, 'dni_extra': dni_extra,
         'am_abs': am_abs},
        index=times
    )
    # calculate total irradiance using PVLIB
    total_irrad = pvlib.irradiance.total_irrad(
        surface_tilt, surface_azimuth, df['solar_zenith'], df['solar_azimuth'],
        df['dni'], df['ghi'], df['dhi'], dni_extra=df['dni_extra'],
        airmass=df['am_abs'], model=model
    ).fillna(0.0)
    # convert to ndarrays
    poa_global = total_irrad['poa_global'].values
    poa_direct = total_irrad['poa_direct'].values
    poa_diffuse = total_irrad['poa_diffuse'].values
    return poa_global, poa_direct, poa_diffuse
