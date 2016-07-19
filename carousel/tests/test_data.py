"""
Test data sources
"""

from nose.tools import ok_, eq_
from carousel.core.data_sources import DataSource
from carousel.core.data_readers import XLRDReader
from carousel.tests import PROJ_PATH, TESTS_DIR
import os

TUSCON = os.path.join(PROJ_PATH, 'data', 'Tuscon.json')
XLRDREADER_TESTDATA = os.path.join(TESTS_DIR, 'xlrdreader_testdata.xlsx')


def test_datasource_metaclasss():
    """
    Test data source meta class.
    """

    class DataSourceTest1(DataSource):
        """
        Test data source with parameters in file.
        """
        data_file = 'pvpower.json'
        data_path = os.path.join(PROJ_PATH, 'data')

        def __prepare_data__(self):
            pass

    data_test1 = DataSourceTest1(TUSCON)
    ok_(isinstance(data_test1, DataSource))
    eq_(data_test1.param_file, os.path.join(PROJ_PATH, 'data', 'pvpower.json'))

    class DataSourceTest2(DataSource):
        """
        Test data source with parameters in code.
        """
        latitude = {
            "description": "latitude",
            "units": "degrees",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        }
        longitude = {
            "description": "longitude",
            "units": "degrees",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        }
        elevation = {
            "description": "altitude of site above sea level",
            "units": "meters",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
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
            "dtype": "float",
            "uncertainty": 1.0
        }
        Uwind = {
            "description": "average yearly wind speed",
            "units": "m/s",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        }
        surface_azimuth = {
            "description": "site rotation",
            "units": "degrees",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        }
        timezone = {
            "description": "timezone",
            "isconstant": True,
            "dtype": "str"
        }

        def __prepare_data__(self):
            pass

    data_test2 = DataSourceTest2(TUSCON)
    ok_(isinstance(data_test2, DataSource))
    for k, val in data_test1.parameters.iteritems():
        eq_(data_test2.parameters[k], val)


def test_xlrdreader_datasource():
    """
    Test data source with xlrd reader.
    """

    class DataSourceTest3(DataSource):
        """
        Test data source with xlrd reader and params in file.
        """
        data_reader = XLRDReader
        data_file = 'xlrdreader_param.json'
        data_path = TESTS_DIR

        def __prepare_data__(self):
            pass

    data_test3 = DataSourceTest3(XLRDREADER_TESTDATA)
    ok_(isinstance(data_test3, DataSource))
    eq_(data_test3.data_reader, XLRDReader)
