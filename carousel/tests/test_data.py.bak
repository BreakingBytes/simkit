"""
Test data sources
"""

from nose.tools import ok_, eq_
from carousel.tests import logging
from carousel.core import UREG
from carousel.core.data_sources import DataSource, DataParameter
from carousel.core.data_readers import XLRDReader
from carousel.tests import PROJ_PATH, TESTS_DIR
import os

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
TUSCON = os.path.join(PROJ_PATH, 'data', 'Tuscon.json')
XLRDREADER_TESTDATA = os.path.join(TESTS_DIR, 'xlrdreader_testdata.xlsx')


def test_datasource_metaclass():
    """
    Test data source meta class.
    """

    class DataSourceTest1(DataSource):
        """
        Test data source with parameters in file.
        """
        class Meta:
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
        latitude = DataParameter(**{
            "description": "latitude",
            "units": "degrees",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        })
        longitude = DataParameter(**{
            "description": "longitude",
            "units": "degrees",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        })
        elevation = DataParameter(**{
            "description": "altitude of site above sea level",
            "units": "meters",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        })
        timestamp_start = DataParameter(**{
            "description": "initial timestamp",
            "isconstant": True,
            "dtype": "datetime"
        })
        timestamp_count = DataParameter(**{
            "description": "number of timesteps",
            "isconstant": True,
            "dtype": "int"
        })
        module = DataParameter(**{
            "description": "PV module",
            "isconstant": True,
            "dtype": "str"
        })
        inverter = DataParameter(**{
            "description": "PV inverter",
            "isconstant": True,
            "dtype": "str"
        })
        module_database = DataParameter(**{
            "description": "module databases",
            "isconstant": True,
            "dtype": "str"
        })
        inverter_database = DataParameter(**{
            "description": "inverter database",
            "isconstant": True,
            "dtype": "str"
        })
        Tamb = DataParameter(**{
            "description": "average yearly ambient air temperature",
            "units": "degC",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        })
        Uwind = DataParameter(**{
            "description": "average yearly wind speed",
            "units": "m/s",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        })
        surface_azimuth = DataParameter(**{
            "description": "site rotation",
            "units": "degrees",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        })
        timezone = DataParameter(**{
            "description": "timezone",
            "isconstant": True,
            "dtype": "str"
        })

        def __prepare_data__(self):
            pass

    data_test2 = DataSourceTest2(TUSCON)
    ok_(isinstance(data_test2, DataSource))
    for k, val in data_test1.parameters.iteritems():
        eq_(data_test2.parameters[k], val)

    class DataSourceTest4(DataSource):
        """
        Test data source with parameters in file.
        """
        latitude = DataParameter(**{
            "description": "latitude",
            "units": "radians",
            "isconstant": True,
            "dtype": "float",
            "uncertainty": 1.0
        })

        class Meta:
            data_file = 'pvpower.json'
            data_path = os.path.join(PROJ_PATH, 'data')

        def __prepare_data__(self):
            pass


    data_test4 = DataSourceTest4(TUSCON)
    ok_(isinstance(data_test4, DataSource))
    eq_(data_test4['latitude'].u, UREG.radians)
    eq_(data_test4.param_file, os.path.join(PROJ_PATH, 'data', 'pvpower.json'))


def test_xlrdreader_datasource():
    """
    Test data source with xlrd reader.
    """

    class DataSourceTest3(DataSource):
        """
        Test data source with xlrd reader and params in file.
        """
        class Meta:
            data_reader = XLRDReader
            data_file = 'xlrdreader_param.json'
            data_path = TESTS_DIR

        def __prepare_data__(self):
            pass

    data_test3 = DataSourceTest3(XLRDREADER_TESTDATA)
    ok_(isinstance(data_test3, DataSource))
    eq_(data_test3._meta.data_reader, XLRDReader)
    os.remove(os.path.join(TESTS_DIR, 'xlrdreader_testdata.xlsx.json'))
    LOGGER.debug('xlrdreader_testdata.xlsx.json has been cleaned')


if __name__ == '__main__':
    test_datasource_metaclass()
    test_xlrdreader_datasource()
