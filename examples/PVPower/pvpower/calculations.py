"""
Calculations for PV Power demo
"""

from circus.core.calculations import Calc
import os
from pvpower import PROJ_PATH

CALC_PATH = os.path.join(PROJ_PATH, 'calculations')


class UtilityCalcs(Calc):
    calcs_file = 'utils.json'
    calcs_path = CALC_PATH


class PerformanceCalcs(Calc):
    calcs_file = 'performance.json'
    calcs_path = CALC_PATH


class IrradianceCalcs(Calc):
    calcs_file = 'irradiance.json'
    calcs_path = CALC_PATH
