# -*- coding: utf-8 -*-

"""
This module contains formulas for calculating
"""

import numpy as np
import pvlib

from pvsimlife.pvsimlife_lib import convert_args, Celsius_to_Kelvin


def f_Pac(inverter, Vmp, Pmp):
    """
    Calculate AC power
    """
    return pvlib.pvsystem.snlinverter(inverter, Vmp, Vmp)


def f_Pdc():
    """
    Calculate DC power
    """
    dc = pvlib.pvsystem.sapm(
        module, total_irrad['poa_direct'], total_irrad['poa_diffuse'],
        temps['temp_cell'], am_abs, aoi
    )

