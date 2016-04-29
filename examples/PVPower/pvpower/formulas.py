"""
Formulas for PV Power demo
"""

from circus.core.formulas import Formula
import os
from pvpower import PROJ_PATH

FORMULA_PATH = os.path.join(PROJ_PATH, 'formulas')


class UtilityFormulas(Formula):
    formulas_file = 'utils.json'
    formulas_path = FORMULA_PATH


class PerformanceFormulas(Formula):
    formulas_file = 'performance.json'
    formulas_path = FORMULA_PATH


class IrradianceFormulas(Formula):
    formulas_file = 'irradiance.json'
    formulas_path = FORMULA_PATH
