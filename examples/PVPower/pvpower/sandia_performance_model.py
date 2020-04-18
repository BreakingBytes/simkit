"""
Sandia Performance Model
"""

from simkit.core.data_sources import DataSource
from simkit.core.formulas import Formula
from simkit.core.calculations import Calc
from simkit.core.calculators import Calculator
from simkit.core.outputs import Output
from simkit.core.simulations import Simulation
from simkit.core.models import Model
from simkit.core import UREG
from datetime import datetime
import pvlib
import os
from pvpower import PROJ_PATH

CALC_PATH = os.path.join(PROJ_PATH, 'calculations')
FORMULA_PATH = os.path.join(PROJ_PATH, 'formulas')
DATA_PATH = os.path.join(PROJ_PATH, 'data')
SANDIA_MODULES = os.path.join(PROJ_PATH, 'Sandia Modules.csv')
CEC_MODULES = os.path.join(PROJ_PATH, 'CEC Modules.csv')
CEC_INVERTERS = os.path.join(PROJ_PATH, 'CEC Inverters.csv')


class PVPowerData(DataSource):
    """
    Data sources for PV Power demo.
    """
    class Meta:
        data_file = 'pvpower.json'
        data_path = DATA_PATH

    def __prepare_data__(self):
        parameters = getattr(self, 'parameters')
        # set frequencies
        for k in ('HOURLY', 'MONTHLY', 'YEARLY'):
            self.data[k] = k
            self.isconstant[k] = True
        # apply metadata
        for k, v in parameters.items():
            # TODO: this should be applied in data reader using _meta_names from
            # data registry which should use a meta class and all parameter
            # files should have same layout even xlrd and numpy readers, etc.
            if 'isconstant' in v:
                self.isconstant[k] = v['isconstant']
            # uncertainty is dictionary
            if 'uncertainty' in v:
                self.uncertainty[k] = {k: v['uncertainty'] * UREG.percent}
        # convert initial timestamp to datetime
        self.data['timestamp_start'] = datetime(*self.data['timestamp_start'])
        # get module and inverter databases
        self.data['module_database'] = pvlib.pvsystem.retrieve_sam(
            self.data['module_database'], path=SANDIA_MODULES
        )
        self.data['inverter_database'] = pvlib.pvsystem.retrieve_sam(
            self.data['inverter_database'], path=CEC_INVERTERS
        )
        # get module and inverter
        self.data['module'] = self.data['module_database'][self.data['module']]
        self.data['inverter'] = (
            self.data['inverter_database'][self.data['inverter']]
        )


class UtilityFormulas(Formula):
    """
    Formulas for PV Power demo
    """
    class Meta:
        formulas_file = 'utils.json'
        formulas_path = FORMULA_PATH


class PerformanceFormulas(Formula):
    """
    Formulas for performance calcs
    """
    class Meta:
        formulas_file = 'performance.json'
        formulas_path = FORMULA_PATH


class IrradianceFormulas(Formula):
    """
    Formulas for irradiance calcs
    """
    class Meta:
        formulas_file = 'irradiance.json'
        formulas_path = FORMULA_PATH


class UtilityCalcs(Calc):
    """
    Calculations for PV Power demo
    """
    class Meta:
        calcs_file = 'utils.json'
        calcs_path = CALC_PATH
        dependencies = ['PerformanceCalcs']
        calculator = Calculator
        is_dynamic = False


class PerformanceCalcs(Calc):
    """
    Calculations for performance
    """
    class Meta:
        calcs_file = 'performance.json'
        calcs_path = CALC_PATH
        dependencies = ['IrradianceCalcs']
        calculator = Calculator
        is_dynamic = False


class IrradianceCalcs(Calc):
    """
    Calculations for irradiance
    """
    class Meta:
        calcs_file = 'irradiance.json'
        calcs_path = CALC_PATH
        calculator = Calculator
        is_dynamic = False


class PVPowerOutputs(Output):
    """
    Outputs for PV Power demo
    """
    class Meta:
        outputs_file = 'pvpower.json'
        outputs_path = os.path.join(PROJ_PATH, 'outputs')


class PerformanceOutputs(Output):
    """
    Performance outputs for PV Power demo
    """
    class Meta:
        outputs_file = 'performance.json'
        outputs_path = os.path.join(PROJ_PATH, 'outputs')


class IrradianceOutputs(Output):
    """
    Irradiance outputs for PV Power demo
    """
    class Meta:
        outputs_file = 'irradiance.json'
        outputs_path = os.path.join(PROJ_PATH, 'outputs')


class Standalone(Simulation):
    """
    PV Power Demo Simulations
    """
    pass


class SAPM(Model):
    """
    PV Power Demo model
    """
    class Meta:
        modelpath = PROJ_PATH  # folder containing project, not model
