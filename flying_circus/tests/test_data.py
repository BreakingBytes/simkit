"""
Test data sources
"""

from nose.tools import ok_, eq_
from flying_circus.core.data_sources import DataSource
from flying_circus.tests import PROJ_PATH
import os

TUSCON = os.path.join(PROJ_PATH, 'data', 'Tuscon.json')


def test_datasource_metaclasss():

    class DataSourceTest1(DataSource):
        data_file = 'pvpower.json'
        data_path = os.path.join(PROJ_PATH, 'data')

        def __prepare_data__(self):
            pass

    data_test1 = DataSourceTest1(TUSCON)
    ok_(isinstance(data_test1, DataSource))
    eq_(data_test1.param_file, os.path.join(PROJ_PATH, 'data', 'pvpower.json'))

    class DataSourceTest2(DataSource):
        latitude = {
            "description": "latitude",
            "units": "degrees",
            "isconstant": True,
            "dtype": "float"
        }
        longitude = {
            "description": "longitude",
            "units": "degrees",
            "isconstant": True,
            "dtype": "float"
        }
        elevation = {
            "description": "altitude of site above sea level",
            "units": "meters",
            "isconstant": True,
            "dtype": "float"
        }
        timestamp_start = {
            "description": "initial timestamp",
            "isconstant": True,
            "dtype": "datetime"
        }
        timestamp_count = {
            "description": "number of timesteps",
            "isconstant": True,
            "dtype": "int"
        }
        module = {
            "description": "PV module",
            "isconstant": True,
            "dtype": "str"
        }
        inverter = {
            "description": "PV inverter",
            "isconstant": True,
            "dtype": "str"
        }
        module_database = {
            "description": "module databases",
            "isconstant": True,
            "dtype": "str"
        }
        inverter_database = {
            "description": "inverter database",
            "isconstant": True,
            "dtype": "str"
        }
        Tamb = {
            "description": "average yearly ambient air temperature",
            "units": "degC",
            "isconstant": True,
            "dtype": "float"
        }
        Uwind = {
            "description": "average yearly wind speed",
            "units": "m/s",
            "isconstant": True,
            "dtype": "float"
        }
        surface_azimuth = {
            "description": "altitude of site above sea level",
            "units": "degrees",
            "isconstant": True,
            "dtype": "float"
        }

        def __prepare_data__(self):
            pass

    data_test2 = DataSourceTest2(TUSCON)
    ok_(isinstance(data_test2, DataSource))
    for k, v in data_test2.parameters.iteritems():
        eq_(data_test2.parameters[k], v)
