"""
New Style Carousel Sandia Performance Model
"""

from carousel.core.data_sources import DataSourceBase, DataSource, DataParameter
from carousel.core.formulas import Formula, FormulaParameter
from carousel.core.calculations import Calc, CalcParameter
from carousel.core.calculators import Calculator
from carousel.core.outputs import Output, OutputParameter
from carousel.core.simulations import Simulation, SimParameter
from carousel.core.models import Model, ModelParameter
from carousel.core import UREG
from datetime import datetime
import pvlib
import os
from pvpower import PROJ_PATH

SANDIA_MODULES = os.path.join(PROJ_PATH, 'Sandia Modules.csv')
CEC_MODULES = os.path.join(PROJ_PATH, 'CEC Modules.csv')
CEC_INVERTERS = os.path.join(PROJ_PATH, 'CEC Inverters.csv')


class PVPowerData(DataSource):
    """
    Data sources for PV Power demo.
    """
    latitude = DataParameter(units="degrees", uncertainty=1.0)
    longitude = DataParameter(units="degrees", uncertainty=1.0)
    elevation = DataParameter(units="meters", uncertainty=1.0)
    timestamp_start = DataParameter()
    timestamp_count = DataParameter()
    module = DataParameter()
    inverter = DataParameter()
    module_database = DataParameter()
    inverter_database = DataParameter()
    Tamb = DataParameter(units="degC", uncertainty=1.0)
    Uwind = DataParameter(units="m/s", uncertainty=1.0)
    surface_azimuth = DataParameter(units="degrees", uncertainty=1.0)
    timezone = DataParameter()

    def __prepare_data__(self):
        parameters = getattr(self, DataSourceBase._param_attr)
        # set frequencies
        for k in ('HOURLY', 'MONTHLY', 'YEARLY'):
            self.data[k] = k
            self.isconstant[k] = True
        # apply metadata
        for k, v in parameters.iteritems():
            # TODO: this should be applied in data reader using _meta_names from
            # data registry which should use a meta class and all parameter
            # files should have same layout even xlrd and numpy readers, etc.
            self.isconstant[k] = True  # set all data "isconstant" True
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
    f_daterange = FormulaParameter()
    f_energy = FormulaParameter(
        args=["ac_power", "times"],
        units=[["watt_hour", None], ["W", None]]
    )
    f_rollup = FormulaParameter(
        args=["items", "times", "freq"],
        units=["=A", ["=A", None, None]]
    )

    class Meta:
        module = ".utils"
        package = "formulas"


class PerformanceFormulas(Formula):
    """
    Formulas for performance calcs
    """
    f_ac_power = FormulaParameter(
        args=["inverter", "v_mp", "p_mp"],
        units=["W", [None, "V", "W"]]
    )
    f_dc_power = FormulaParameter(
        args=["effective_irradiance", "cell_temp", "module"],
        units=[["A", "A", "V", "V", "W"], ["suns", "degC", None]]
    )
    f_effective_irradiance = FormulaParameter(
        args=["poa_direct", "poa_diffuse", "am_abs", "aoi", "module"],
        units=["suns", ["W/m**2", "W/m**2", "dimensionless", "deg", None]]
    )
    f_cell_temp = FormulaParameter(
        args=["poa_global", "wind_speed", "air_temp"],
        units=[["degC", "degC"], ["W/m**2", "m/s", "degC"]]
    )
    f_aoi = FormulaParameter(
        args=["surface_tilt", "surface_azimuth", "solar_zenith",
              "solar_azimuth"],
        units=["deg", ["deg", "deg", "deg", "deg"]]
    )

    class Meta:
        module = ".performance"
        package = "formulas"


class IrradianceFormulas(Formula):
    """
    Formulas for irradiance calcs
    """
    f_linketurbidity = FormulaParameter(
        args=["times", "latitude", "longitude"],
        units=["dimensionless", [None, "deg", "deg"]],
        isconstant=["times"]
    )
    f_clearsky = FormulaParameter(
        args=["solar_zenith", "am_abs", "tl", "dni_extra", "altitude"],
        units=[
            ["W/m**2", "W/m**2", "W/m**2"],
            ["deg", "dimensionless", "dimensionless", "W/m**2", "m"]
        ],
        isconstant=["dni_extra"]
    )
    f_solpos = FormulaParameter(
        args=["times", "latitude", "longitude"],
        units=[["degree", "degree"], [None, "degree", "degree"]],
        isconstant=["times"]
    )
    f_dni_extra = FormulaParameter(args=["times"], units=["W/m**2", [None]])
    f_airmass = FormulaParameter(
        args=["solar_zenith"], units=["dimensionless", ["deg"]],
        isconstant=[]
    )
    f_pressure = FormulaParameter(
        args=["altitude"], units=["Pa", ["m"]], isconstant=[]
    )
    f_am_abs = FormulaParameter(
        args=["airmass", "pressure"],
        units=["dimensionless", ["dimensionless", "Pa"]],
        isconstant=[]
    )
    f_total_irrad = FormulaParameter(
        args=[
            "times", "surface_tilt", "surface_azimuth", "solar_zenith",
            "solar_azimuth", "dni", "ghi", "dhi", "dni_extra", "am_abs"
        ],
        units=[
            ["W/m**2", "W/m**2", "W/m**2"],
            [
                None, "deg", "deg", "deg", "deg", "W/m**2", "W/m**2",
                "W/m**2",
                "W/m**2", "dimensionless"
            ]
        ],
        isconstant=["times", "dni_extra"]
    )

    class Meta:
        module = ".irradiance"
        package = "formulas"


class UtilityCalcs(Calc):
    """
    Calculations for PV Power demo
    """
    energy = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["ac_power", "daterange"],
        formula="f_energy",
        args={"outputs": {"ac_power": "Pac", "times": "timestamps"}},
        returns=["hourly_energy", "hourly_timeseries"]
    )
    monthly_rollup = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["energy"],
        formula="f_rollup",
        args={
            "data": {"freq": "MONTHLY"},
            "outputs": {"items": "hourly_energy",
                        "times": "hourly_timeseries"}
        },
        returns=["monthly_energy"]
    )
    yearly_rollup = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["energy"],
        formula="f_rollup",
        args={"data": {"freq": "YEARLY"},
              "outputs": {"items": "hourly_energy",
                          "times": "hourly_timeseries"}},
        returns=["annual_energy"]
    )


class PerformanceCalcs(Calc):
    """
    Calculations for performance
    """
    aoi = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["solpos"],
        formula="f_aoi",
        args={"data": {"surface_tilt": "latitude",
                       "surface_azimuth": "surface_azimuth"},
              "outputs": {"solar_zenith": "solar_zenith",
                          "solar_azimuth": "solar_azimuth"}},
        returns=["aoi"]
    )
    cell_temp = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["total_irradiance"],
        formula="f_cell_temp",
        args={"data": {"wind_speed": "Uwind", "air_temp": "Tamb"},
              "outputs": {"poa_global": "poa_global"}},
        returns=["Tcell", "Tmod"]
    )
    effective_irradiance = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["total_irradiance", "aoi", "abs_airmass"],
        formula="f_effective_irradiance",
        args={"data": {"module": "module"},
              "outputs": {"poa_direct": "poa_direct",
                          "poa_diffuse": "poa_diffuse", "am_abs": "am_abs",
                          "aoi": "aoi"}},
        returns=["Ee"]
    )
    dc_power = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["effective_irradiance", "cell_temp"],
        formula="f_dc_power",
        args={"data": {"module": "module"},
              "outputs": {"effective_irradiance": "Ee", "cell_temp": "Tcell"}},
        returns=["Isc", "Imp", "Voc", "Vmp", "Pmp"]
    )
    ac_power = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["dc_power"],
        formula="f_ac_power",
        args={"data": {"inverter": "inverter"},
              "outputs": {"v_mp": "Vmp", "p_mp": "Pmp"}},
        returns=["Pac"]
    )


class IrradianceCalcs(Calc):
    """
    Calculations for irradiance
    """
    daterange = CalcParameter(
        is_dynamic='false',
        calculator=Calculator,
        formula="f_daterange",
        args={"data": {"freq": "HOURLY", "dtstart": "timestamp_start",
                       "count": "timestamp_count", "tz": "timezone"}},
        returns=["timestamps"]
    )
    solpos = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["daterange"],
        formula="f_solpos",
        args={"data": {"latitude": "latitude", "longitude": "longitude"},
              "outputs": {"times": "timestamps"}},
        returns=["solar_zenith", "solar_azimuth"]
    )
    extraterrestrial = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["daterange"],
        formula="f_dni_extra",
        args={"outputs": {"times": "timestamps"}},
        returns=["extraterrestrial"]
    )
    airmass = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["solpos"],
        formula="f_airmass",
        args={"outputs": {"solar_zenith": "solar_zenith"}},
        returns=["airmass"]
    )
    pressure = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        formula="f_pressure",
        args={"data": {"altitude": "elevation"}},
        returns=["pressure"]
    )
    abs_airmass = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["airmass", "pressure"],
        formula="f_am_abs",
        args={"outputs": {"airmass": "airmass", "pressure": "pressure"}},
        returns=["am_abs"]
    )
    linke_turbidity = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=["daterange"],
        formula="f_linketurbidity",
        args={"data": {"latitude": "latitude", "longitude": "longitude"},
              "outputs": {"times": "timestamps"}},
        returns=["tl"]
    )
    clearsky = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=[
          "solpos", "abs_airmass", "linke_turbidity", "extraterrestrial"
        ],
        formula="f_clearsky",
        args={"data": {"altitude": "elevation"},
              "outputs": {"solar_zenith": "solar_zenith", "am_abs": "am_abs",
                          "tl": "tl", "dni_extra": "extraterrestrial"}},
        returns=["dni", "ghi", "dhi"]
    )
    total_irradiance = CalcParameter(
        is_dynamic="false",
        calculator=Calculator,
        dependencies=[
          "daterange", "solpos", "clearsky", "extraterrestrial",
          "abs_airmass"
        ],
        formula="f_total_irrad",
        args={
            "data": {
                "surface_tilt": "latitude", "surface_azimuth": "surface_azimuth"
            },
            "outputs": {
                "times": "timestamps", "solar_zenith": "solar_zenith",
                "solar_azimuth": "solar_azimuth", "dni": "dni",
                "ghi": "ghi", "dhi": "dhi", "dni_extra": "extraterrestrial",
                "am_abs": "am_abs"
            }
        },
        returns=["poa_global", "poa_direct", "poa_diffuse"]
    )


class PVPowerOutputs(Output):
    """
    Outputs for PV Power demo
    """
    timestamps = OutputParameter(isconstant=True, size=8761)
    hourly_energy = OutputParameter(
        isconstant=True, timeseries="hourly_timeseries", units="W*h", size=8760
    )
    hourly_timeseries = OutputParameter(isconstant=True, units="W*h", size=8760)
    monthly_energy = OutputParameter(isconstant=True, units="W*h", size=12)
    annual_energy = OutputParameter(isconstant=True, units="W*h")


class PerformanceOutputs(Output):
    """
    Performance outputs for PV Power demo
    """
    Pac = OutputParameter(
        isconstant=True, timeseries="timestamps", units="W", size=8761
    )
    Isc = OutputParameter(
        isconstant=True, timeseries="timestamps", units="A", size=8761
    )
    Imp = OutputParameter(
        isconstant=True, timeseries="timestamps", units="A", size=8761
    )
    Voc = OutputParameter(
        isconstant=True, timeseries="timestamps", units="V", size=8761
    )
    Vmp = OutputParameter(
        isconstant=True, timeseries="timestamps", units="V", size=8761
    )
    Pmp = OutputParameter(
        isconstant=True, timeseries="timestamps", units="W", size=8761
    )
    Ee = OutputParameter(
        isconstant=True, timeseries="timestamps", units="dimensionless",
        size=8761
    )
    Tcell = OutputParameter(
        isconstant=True, timeseries="timestamps", units="degC", size=8761
    )
    Tmod = OutputParameter(
        isconstant=True, timeseries="timestamps", units="degC", size=8761
    )


class IrradianceOutputs(Output):
    """
    Irradiance outputs for PV Power demo
    """
    tl = OutputParameter(
        isconstant=True, timeseries="timestamps", units="dimensionless",
        size=8761
    )
    poa_global = OutputParameter(
        isconstant=True, timeseries="timestamps", units="W/m**2", size=8761
    )
    poa_direct = OutputParameter(
        isconstant=True, timeseries="timestamps", units="W/m**2", size=8761
    )
    poa_diffuse = OutputParameter(
        isconstant=True, timeseries="timestamps", units="W/m**2", size=8761
    )
    aoi = OutputParameter(
        isconstant=True, timeseries="timestamps", units="deg", size=8761
    )
    solar_zenith = OutputParameter(
        isconstant=True, timeseries="timestamps", units="deg", size=8761
    )
    solar_azimuth = OutputParameter(
        isconstant=True, timeseries="timestamps", units="deg", size=8761
    )
    pressure = OutputParameter(
        isconstant=True, timeseries="timestamps", units="Pa", size=1
    )
    airmass = OutputParameter(
        isconstant=True, timeseries="timestamps", units="dimensionless",
        size=8761
    )
    am_abs = OutputParameter(
        isconstant=True, timeseries="timestamps", units="dimensionless",
        size=8761
    )
    extraterrestrial = OutputParameter(
        isconstant=True, timeseries="timestamps", units="W/m**2", size=8761
    )
    dni = OutputParameter(
        isconstant=True, timeseries="timestamps", units="W/m**2", size=8761
    )
    dhi = OutputParameter(
        isconstant=True, timeseries="timestamps", units="W/m**2", size=8761
    )
    ghi = OutputParameter(
        isconstant=True, timeseries="timestamps", units="W/m**2", size=8761
    )


class PVPowerSim(Simulation):
    """
    PV Power Demo Simulations
    """
    settings = SimParameter(
        ID="Tuscon_SAPM",
        path="~/Carousel_Simulations",
        thresholds=None,
        interval=[1, "hour"],
        sim_length=[0, "hours"],
        write_frequency=0,
        write_fields={
            "data": ["latitude", "longitude", "Tamb", "Uwind"],
            "outputs": ["monthly_energy", "annual_energy"]
        },
        display_frequency=12,
        display_fields={
            "data": ["latitude", "longitude", "Tamb", "Uwind"],
            "outputs": ["monthly_energy", "annual_energy"]
        },
        commands=['start', 'pause']
    )


class NewSAPM(Model):
    """
    PV Power Demo model
    """
    class Meta:
        modelpath = PROJ_PATH  # folder containing project, not model
    data = ModelParameter(
        layer='Data', sources=[(PVPowerData, {'filename': 'Tuscon.json'})]
    )
    outputs = ModelParameter(
        layer='Outputs',
        sources=[PVPowerOutputs, PerformanceOutputs, IrradianceOutputs]
    )
    formulas = ModelParameter(
        layer='Formulas',
        sources=[UtilityFormulas, PerformanceFormulas, IrradianceFormulas]
    )
    calculations = ModelParameter(
        layer='Calculations',
        sources=[UtilityCalcs, PerformanceCalcs, IrradianceCalcs]
    )
    simulations = ModelParameter(layer='Simulations', sources=[PVPowerSim])
