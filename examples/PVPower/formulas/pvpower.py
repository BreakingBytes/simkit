# -*- coding: utf-8 -*-

"""
This module contains formulas for calculating
"""

import pvlib


def f_Pac(inverter, Vmp, Pmp):
    """
    Calculate AC power
    """
    return pvlib.pvsystem.snlinverter(inverter, Vmp, Pmp)


def f_Pdc(module, poa_direct, poa_diffuse, cell_temp, am_abs, aoi):
    """
    Calculate DC power
    """
    dc = pvlib.pvsystem.sapm(
        module, poa_direct, poa_diffuse, cell_temp, am_abs, aoi
    )
    return dc['i_sc'], dc['i_mp'], dc['v_oc'], dc['v_mp'], dc['p_mp'], Ee

