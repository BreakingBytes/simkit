"""
Test data sources
"""

from nose.tools import ok_, eq_, raises
from circus.core.data_sources import DataSource
from circus.tests import PROJ_PATH
import os


def test_datasource_metaclasss():

    class DataSourceTest1(DataSource):
        data_file = 'pvpower.json'
        data_path = os.path.join(PROJ_PATH, 'data')
        def prepare_data(self):
            pass

    data_test1 = DataSourceTest1(os.path.join(PROJ_PATH, 'data', 'Tuscon.json'))
    ok_(isinstance(data_test1, DataSource))
    eq_(data_test1.param_file, os.path.join(PROJ_PATH, 'data', 'pvpower.json'))
