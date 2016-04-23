"""
Calculations for PV Power demo
"""

from circus.core.calculations import Calc
import os
from pvpower import PROJ_PATH


class PVPowerCalcs(Calc):
    outputs_file = 'pvpower.json'
    outputs_path = os.path.join(PROJ_PATH, 'calculations')


class PVerformanceCalcs(Calc):
    outputs_file = 'performance.json'
    outputs_path = os.path.join(PROJ_PATH, 'calculations')


class IrradianceCalcs(Calc):
    outputs_file = 'irradiance.json'
    outputs_path = os.path.join(PROJ_PATH, 'calculations')
