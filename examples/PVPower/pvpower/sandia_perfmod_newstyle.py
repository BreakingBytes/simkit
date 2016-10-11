"""
New Style Carousel Sandia Performance Model
"""

from carousel.core.data_sources import DataSource
from carousel.core.formulas import Formula
from carousel.core.calculations import Calc
from carousel.core.outputs import Output
from carousel.core.simulations import Simulation
from carousel.core.models import Model
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
    latitude = {"units": "degrees", "uncertainty": 1.0}
    longitude = {"units": "degrees", "uncertainty": 1.0}
    elevation = {"units": "meters", "uncertainty": 1.0}
    timestamp_start = {}
    timestamp_count = {}
    module = {}
    inverter = {}
    module_database = {}
    inverter_database = {}
    Tamb = {"units": "degC", "uncertainty": 1.0}
    Uwind = {"units": "m/s", "uncertainty": 1.0}
    surface_azimuth = {"units": "degrees", "uncertainty": 1.0}
    timezone = {}

    def __prepare_data__(self):
        # set frequencies
        for k in ('HOURLY', 'MONTHLY', 'YEARLY'):
            self.data[k] = k
            self.isconstant[k] = True
        # apply metadata
        for k, v in self.parameters.iteritems():
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
    module = ".utils"
    package = "formulas"
    formulas = {
        "f_daterange": None,
        "f_energy": {
            "args": ["ac_power", "times"],
            "units": [["watt_hour", None], ["W", None]]
        },
        "f_rollup": {
            "args": ["items", "times", "freq"],
            "units": ["=A", ["=A", None, None]]
        }
    }


class PerformanceFormulas(Formula):
    """
    Formulas for performance calcs
    """
    module = ".performance"
    package = "formulas"
    formulas = {
        "f_ac_power": {
            "args": ["inverter", "v_mp", "p_mp"],
            "units": ["W", [None, "V", "W"]]
        },
        "f_dc_power": {
            "args": [
                "effective_irradiance", "cell_temp", "module"
            ],
            "units": [
                ["A", "A", "V", "V", "W"],
                ["suns", "degC", None]
            ]
        },
        "f_effective_irradiance": {
            "args": ["poa_direct", "poa_diffuse", "am_abs", "aoi", "module"],
            "units": ["suns",
                      ["W/m**2", "W/m**2", "dimensionless", "deg", None]]
        },
        "f_cell_temp": {
            "args": ["poa_global", "wind_speed", "air_temp"],
            "units": [["degC", "degC"], ["W/m**2", "m/s", "degC"]]
        },
        "f_aoi": {
            "args": [
                "surface_tilt", "surface_azimuth", "solar_zenith",
                "solar_azimuth"
            ],
            "units": ["deg", ["deg", "deg", "deg", "deg"]]
        }
    }


class IrradianceFormulas(Formula):
    """
    Formulas for irradiance calcs
    """
    module = ".irradiance"
    package = "formulas"
    formulas = {
        "f_linketurbidity": {
            "args": ["times", "latitude", "longitude"],
            "units": ["dimensionless", [None, "deg", "deg"]],
            "isconstant": ["times"]
        },
        "f_clearsky": {
            "args": ["solar_zenith", "am_abs", "tl", "dni_extra", "altitude"],
            "units": [
                ["W/m**2", "W/m**2", "W/m**2"],
                ["deg", "dimensionless", "dimensionless", "W/m**2", "m"]
            ],
            "isconstant": ["dni_extra"]
        },
        "f_solpos": {
            "args": ["times", "latitude", "longitude"],
            "units": [["degree", "degree"], [None, "degree", "degree"]],
            "isconstant": ["times"]
        },
        "f_dni_extra": {"args": ["times"], "units": ["W/m**2", [None]]},
        "f_airmass": {
            "args": ["solar_zenith"], "units": ["dimensionless", ["deg"]],
            "isconstant": []
        },
        "f_pressure": {
            "args": ["altitude"], "units": ["Pa", ["m"]], "isconstant": []
        },
        "f_am_abs": {
            "args": ["airmass", "pressure"],
            "units": ["dimensionless", ["dimensionless", "Pa"]],
            "isconstant": []
        },
        "f_total_irrad": {
            "args": [
                "times", "surface_tilt", "surface_azimuth", "solar_zenith",
                "solar_azimuth", "dni", "ghi", "dhi", "dni_extra", "am_abs"
            ],
            "units": [
                ["W/m**2", "W/m**2", "W/m**2"],
                [
                    None, "deg", "deg", "deg", "deg", "W/m**2", "W/m**2",
                    "W/m**2",
                    "W/m**2", "dimensionless"
                ]
            ],
            "isconstant": ["times", "dni_extra"]
        }
    }


class UtilityCalcs(Calc):
    """
    Calculations for PV Power demo
    """
    dependencies = ["PerformanceCalcs"]
    static = [
        {
            "formula": "f_energy",
            "args": {
                "outputs": {"ac_power": "Pac", "times": "timestamps"}
            },
            "returns": ["hourly_energy", "hourly_timeseries"]
        },
        {
            "formula": "f_rollup",
            "args": {
                "data": {"freq": "MONTHLY"},
                "outputs": {"items": "hourly_energy",
                            "times": "hourly_timeseries"}
            },
            "returns": ["monthly_energy"]
        },
        {
            "formula": "f_rollup",
            "args": {
                "data": {"freq": "YEARLY"},
                "outputs": {"items": "hourly_energy",
                            "times": "hourly_timeseries"}
            },
            "returns": ["annual_energy"]
        }
    ]


class PerformanceCalcs(Calc):
    """
    Calculations for performance
    """
    dependencies = ["IrradianceCalcs"]
    static = [
        {
            "formula": "f_aoi",
            "args": {
                "data": {
                    "surface_tilt": "latitude",
                    "surface_azimuth": "surface_azimuth"
                },
                "outputs": {
                    "solar_zenith": "solar_zenith",
                    "solar_azimuth": "solar_azimuth"
                }
            },
            "returns": ["aoi"]
        },
        {
            "formula": "f_cell_temp",
            "args": {
                "data": {"wind_speed": "Uwind", "air_temp": "Tamb"},
                "outputs": {"poa_global": "poa_global"}
            },
            "returns": ["Tcell", "Tmod"]
        },
        {
            "formula": "f_effective_irradiance",
            "args": {
                "data": {"module": "module"},
                "outputs": {
                    "poa_direct": "poa_direct", "poa_diffuse": "poa_diffuse",
                    "am_abs": "am_abs", "aoi": "aoi"
                }
            },
            "returns": ["Ee"]
        },
        {
            "formula": "f_dc_power",
            "args": {
                "data": {"module": "module"},
                "outputs": {
                    "effective_irradiance": "Ee", "cell_temp": "Tcell"
                }
            },
            "returns": ["Isc", "Imp", "Voc", "Vmp", "Pmp"]
        },
        {
            "formula": "f_ac_power",
            "args": {
                "data": {"inverter": "inverter"},
                "outputs": {"v_mp": "Vmp", "p_mp": "Pmp"}
            },
            "returns": ["Pac"]
        }
    ]


class IrradianceCalcs(Calc):
    """
    Calculations for irradiance
    """
    static = [
        {
            "formula": "f_daterange",
            "args": {
                "data": {
                    "freq": "HOURLY", "dtstart": "timestamp_start",
                    "count": "timestamp_count", "tz": "timezone"
                }
            },
            "returns": ["timestamps"]
        },
        {
            "formula": "f_solpos",
            "args": {
                "data": {
                    "latitude": "latitude", "longitude": "longitude"
                },
                "outputs": {"times": "timestamps"}
            },
            "returns": ["solar_zenith", "solar_azimuth"]
        },
        {
            "formula": "f_dni_extra",
            "args": {
                "outputs": {"times": "timestamps"}
            },
            "returns": ["extraterrestrial"]
        },
        {
            "formula": "f_airmass",
            "args": {
                "outputs": {"solar_zenith": "solar_zenith"}
            },
            "returns": ["airmass"]
        },
        {
            "formula": "f_pressure",
            "args": {
                "data": {"altitude": "elevation"}
            },
            "returns": ["pressure"]
        },
        {
            "formula": "f_am_abs",
            "args": {
                "outputs": {"airmass": "airmass", "pressure": "pressure"}
            },
            "returns": ["am_abs"]
        },
        {
            "formula": "f_linketurbidity",
            "args": {
                "data": {
                    "latitude": "latitude", "longitude": "longitude"
                },
                "outputs": {"times": "timestamps"}
            },
            "returns": ["tl"]
        },
        {
            "formula": "f_clearsky",
            "args": {
                "data": {"altitude": "elevation"},
                "outputs": {
                    "solar_zenith": "solar_zenith", "am_abs": "am_abs",
                    "tl": "tl",
                    "dni_extra": "extraterrestrial"
                }
            },
            "returns": ["dni", "ghi", "dhi"]
        },
        {
            "formula": "f_total_irrad",
            "args": {
                "data": {
                    "surface_tilt": "latitude",
                    "surface_azimuth": "surface_azimuth"
                },
                "outputs": {
                    "times": "timestamps", "solar_zenith": "solar_zenith",
                    "solar_azimuth": "solar_azimuth", "dni": "dni",
                    "ghi": "ghi",
                    "dhi": "dhi", "dni_extra": "extraterrestrial",
                    "am_abs": "am_abs"
                }
            },
            "returns": ["poa_global", "poa_direct", "poa_diffuse"]
        }
    ]


class PVPowerOutputs(Output):
    """
    Outputs for PV Power demo
    """
    timestamps = {"isconstant": True, "size": 8761}
    hourly_energy = {
        "isconstant": True, "timeseries": "hourly_timeseries",
        "units": "W*h",
        "size": 8760
    }
    hourly_timeseries = {"isconstant": True, "units": "W*h", "size": 8760}
    monthly_energy = {"isconstant": True, "units": "W*h", "size": 12}
    annual_energy = {"isconstant": True, "units": "W*h"}


class PerformanceOutputs(Output):
    """
    Performance outputs for PV Power demo
    """
    Pac = {
        "isconstant": True, "timeseries": "timestamps", "units": "W",
        "size": 8761
    }
    Isc = {
        "isconstant": True, "timeseries": "timestamps", "units": "A",
        "size": 8761
    }
    Imp = {
        "isconstant": True, "timeseries": "timestamps", "units": "A",
        "size": 8761
    }
    Voc = {
        "isconstant": True, "timeseries": "timestamps", "units": "V",
        "size": 8761
    }
    Vmp = {
        "isconstant": True, "timeseries": "timestamps", "units": "V",
        "size": 8761
    }
    Pmp = {
        "isconstant": True, "timeseries": "timestamps", "units": "W",
        "size": 8761
    }
    Ee = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "dimensionless",
        "size": 8761
    }
    Tcell = {
        "isconstant": True, "timeseries": "timestamps", "units": "degC",
        "size": 8761
    }
    Tmod = {
        "isconstant": True, "timeseries": "timestamps", "units": "degC",
        "size": 8761
    }


class IrradianceOutputs(Output):
    """
    Irradiance outputs for PV Power demo
    """
    tl = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "dimensionless",
        "size": 8761
    }
    poa_global = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "W/m**2",
        "size": 8761
    }
    poa_direct = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "W/m**2",
        "size": 8761
    }
    poa_diffuse = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "W/m**2",
        "size": 8761
    }
    aoi = {
        "isconstant": True, "timeseries": "timestamps", "units": "deg",
        "size": 8761
    }
    solar_zenith = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "deg",
        "size": 8761
    }
    solar_azimuth = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "deg",
        "size": 8761
    }
    pressure = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "Pa",
        "size": 1
    }
    airmass = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "dimensionless",
        "size": 8761
    }
    am_abs = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "dimensionless",
        "size": 8761
    }
    extraterrestrial = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "W/m**2",
        "size": 8761
    }
    dni = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "W/m**2",
        "size": 8761
    }
    dhi = {
        "isconstant": True, "timeseries": "timestamps",
        "units": "W/m**2",
        "size": 8761
    }
    ghi = {
        "isconstant": True, "timeseries": "timestamps", "units": "W/m**2",
        "size": 8761
    }


class PVPowerSim(Simulation):
    """
    PV Power Demo Simulations
    """
    ID = "Tuscon_SAPM"
    path = "~/Carousel_Simulations"
    thresholds = None
    interval = [1, "hour"]
    sim_length = [0, "hours"]
    write_frequency = 0
    write_fields = {
        "data": ["latitude", "longitude", "Tamb", "Uwind"],
        "outputs": [
            "monthly_energy", "annual_energy"
        ]
    }
    display_frequency = 12
    display_fields = {
        "data": ["latitude", "longitude", "Tamb", "Uwind"],
        "outputs": [
            "monthly_energy", "annual_energy"
        ]
    }
    commands = ['start', 'pause']


class NewSAPM(Model):
    """
    PV Power Demo model
    """
    modelpath = PROJ_PATH  # folder containing project, not model
    data = [(PVPowerData, {'filename': 'Tuscon.json'})]
    outputs = [PVPowerOutputs, PerformanceOutputs, IrradianceOutputs]
    formulas = [UtilityFormulas, PerformanceFormulas, IrradianceFormulas]
    calculations = [UtilityCalcs, PerformanceCalcs, IrradianceCalcs]
    simulations = [PVPowerSim]
