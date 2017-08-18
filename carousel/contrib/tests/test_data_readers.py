"""
Test contrib data readers.
"""

from carousel.core.data_readers import DataReader
from carousel.contrib.readers import (
    ArgumentReader, DjangoModelReader, HDF5Reader
)
from carousel.core.data_sources import DataSourceBase, DataSource, DataParameter
from datetime import datetime
from carousel.core import UREG
from django.db import models
import django
from django.apps import AppConfig
from django.conf import settings
import sys
import mock
import logging
import h5py
import os
import numpy as np

DIRNAME = os.path.dirname(__file__)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
# test data
TAIR = 25.0
LAT = 38.0
LON = -122.0
TZ = -8.0
H5TEST1 = os.path.join(DIRNAME, 'test1.h5')
H5TEST2 = os.path.join(DIRNAME, 'test2.h5')
H5DTYPE = [('GlobalHorizontalRadiation', '<i8'),
           ('DirectNormalRadiation', '<i8'),
           ('DryBulbTemperature', '<f8')]
H5TABLE = np.array(
    [(0, 0, 15.200897216796875), (0, 0, 14.545711517333984),
     (0, 0, 13.890524864196777), (0, 0, 13.540611267089844),
     (0, 0, 13.190696716308594), (0, 0, 12.942743301391602),
     (0, 0, 12.904003143310547), (115, 566, 14.073929786682129),
     (329, 809, 15.947802543640137), (558, 936, 18.07691764831543),
     (750, 780, 20.15163803100586), (500, 197, 20.636459350585938),
     (510, 147, 21.00153350830078), (531, 139, 21.318157196044922),
     (486, 120, 21.44940757751465), (437, 130, 21.36214256286621),
     (311, 80, 21.034954071044922), (259, 131, 20.530967712402344),
     (124, 106, 19.722484588623047), (4, 0, 18.716384887695312),
     (0, 0, 17.36248207092285), (0, 0, 16.008577346801758),
     (0, 0, 14.654674530029297), (0, 0, 13.30077075958252)],
    dtype=H5DTYPE
)


def setup_hdf5_test_data():
    """
    Set up test data for :func:`test_hdf5_reader`.
    """
    with h5py.File(H5TEST1, 'w') as h5f:
        h5f.create_group('data')
        h5f['data'].create_dataset('GHI',
                                   data=H5TABLE['GlobalHorizontalRadiation'])
        h5f['data'].create_dataset('DNI', data=H5TABLE['DirectNormalRadiation'])
        h5f['data'].create_dataset('Tdry', data=H5TABLE['DryBulbTemperature'])
    with h5py.File(H5TEST2, 'w') as h5f:
        h5f.create_dataset('data', data=H5TABLE)


def teardown_hdf5_test_data():
    """
    Tear down test data for :func:`test_hdf5_reader`.
    """
    os.remove(H5TEST1)
    os.remove(H5TEST2)


class MyApp(AppConfig):
    """
    Dummy Django app necessary to mock a model.
    """
    path = '.'
    name = 'myapp'

# to mock a Django model for testing the DjangoModelReader we need to make a
# dummy Django app and mock a module that contains it
myapp_module = mock.Mock(__name__='myapp', MyApp=MyApp)  # mock module with app
MYAPP = 'myapp.MyApp'  # full path to dummy app
sys.modules['myapp'] = myapp_module  # add mock module to sys.modules
settings.configure()  # configure Django settings
settings.INSTALLED_APPS.append(MYAPP)  # add dummy app to settings
django.setup()  # run Django setup


class MyModel(models.Model):
    """
    Django model for testing
    :class:`~carousel.contrib.readers.DjangoModelReader`.
    """
    air_temp = models.FloatField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    timezone = models.FloatField()
    pvmodule = models.CharField(max_length=20)

    class Meta:
        app_label = MYAPP

MYMODEL = MyModel(air_temp=TAIR, latitude=LAT, longitude=LON,
                  timezone=TZ, pvmodule='SPR E20-327')


def test_arg_reader():
    """
    Test :class:`~carousel.contrib.readers.ArgumentReader` is instantiated and
    can load argument data units and values correctly.

    :return: arg reader and data
    :raises: AssertionError
    """
    pvmodule = {
        'name': 'SPR E20-327',
        'nameplate': 327.0,
        'vintage': datetime(2014, 1, 1)
    }
    air_temp = TAIR
    location = {'latitude': LAT, 'longitude': LON, 'timezone': TZ}
    parameters = {
        'pvmodule': {'extras': {'argpos': 0}},
        'air_temp': {'units': 'celsius', 'extras': {'argpos': 1}},
        'latitude': {'units': 'degrees', 'extras': {}},
        'longitude': {'units': 'degrees', 'extras': {}},
        'timezone': {'units': 'hours', 'extras': {}}
    }
    arg_reader = ArgumentReader(parameters)
    assert isinstance(arg_reader, DataReader)  # instance of ArgumentReader
    assert not arg_reader.is_file_reader  # is not a file reader
    data = arg_reader.load_data(pvmodule, air_temp, **location)
    # loaded parameter units and values are correct
    assert data['air_temp'].magnitude == TAIR
    assert data['air_temp'].units == UREG.degC
    assert data['latitude'].magnitude == LAT
    assert data['latitude'].units == UREG.degree
    assert data['longitude'].magnitude == LON
    assert data['longitude'].units == UREG.degree
    assert data['timezone'].magnitude == TZ
    assert data['timezone'].units == UREG.hour
    return arg_reader, data


def test_arg_data_src():
    """
    Test :class:`carousel.core.data_sources.DataSource` can be instantiated with
    an :class:`~carousel.contrib.readers.ArgumentReader` and that it can

    :return: arg data
    :raises: AssertionError
    """

    class ArgSrcTest(DataSource):
        air_temp = DataParameter(**{'units': 'celsius', 'argpos': 0})
        latitude = DataParameter(**{'units': 'degrees', 'isconstant': True})
        longitude = DataParameter(**{'units': 'degrees', 'isconstant': True})
        timezone = DataParameter(**{'units': 'hours'})

        def __prepare_data__(self):
            pass

        class Meta:
            data_reader = ArgumentReader
            data_cache_enabled = False

    arg_data = ArgSrcTest(TAIR, latitude=LAT, longitude=LON, timezone=TZ)
    assert isinstance(arg_data, DataSource)  # instance of DataSource
    # loaded parameter units and values are correct
    assert arg_data['air_temp'].magnitude == TAIR
    assert arg_data['air_temp'].units == UREG.degC
    assert arg_data['latitude'].magnitude == LAT
    assert arg_data['latitude'].units == UREG.degree
    assert arg_data['longitude'].magnitude == LON
    assert arg_data['longitude'].units == UREG.degree
    assert arg_data['timezone'].magnitude == TZ
    assert arg_data['timezone'].units == UREG.hour
    return arg_data


def test_django_reader():
    """
    Test :class:`~carousel.contrib.readers.DjangoModelReader` is instantiated
    and can load argument data units and values correctly.

    :return: django reader and data
    :raises: AssertionError
    """
    params = {'air_temp': {'units': 'celsius', 'extras': {}}}
    meta = type('Meta', (), {'model': MyModel})
    django_reader = DjangoModelReader(params, meta)
    assert isinstance(django_reader, (DataReader, ArgumentReader))
    assert not django_reader.is_file_reader  # is not a file reader
    data = django_reader.load_data(MYMODEL)
    LOGGER.debug('air temp = %s', data['air_temp'])
    assert data['air_temp'].magnitude == TAIR
    assert data['air_temp'].units == UREG.degC
    return django_reader, data


def test_django_data_src():
    """
    Test Django model reader data source.

    :raises: AssertionError

    Test data source is created from Django model fields, parameters have
    correct units and magnitude and ``field`` and ``exclude`` meta options
    work right.
    """

    class DjangoSrcTest1(DataSource):
        """
        Data source from Django model that specifies fields.
        """
        # parameters
        air_temp = DataParameter(**{'units': 'celsius'})
        latitude = DataParameter(**{'units': 'degrees'})
        longitude = DataParameter(**{'units': 'degrees'})

        class Meta:
            data_reader = DjangoModelReader
            data_cache_enabled = False
            model = MyModel
            fields = ('air_temp', 'latitude', 'longitude')

        def __prepare_data__(self):
            pass

    django_data1 = DjangoSrcTest1(MYMODEL)
    django_data1_parameters = getattr(django_data1, DataSourceBase._param_attr)
    assert isinstance(django_data1, DataSource)
    LOGGER.debug('air temp = %s', django_data1['air_temp'])
    assert django_data1['air_temp'].magnitude == TAIR
    assert django_data1['air_temp'].units == UREG.celsius
    assert 'latitude' in django_data1_parameters
    assert 'longitude' in django_data1_parameters
    assert 'timezone' not in django_data1_parameters
    assert 'pvmodule' not in django_data1_parameters

    class DjangoSrcTest2(DataSource):
        """
        Data source from Django model that excludes fields.
        """
        # parameters
        air_temp = DataParameter(**{'units': 'celsius'})
        latitude = DataParameter(**{'units': 'degrees'})
        longitude = DataParameter(**{'units': 'degrees'})

        class Meta:
            data_reader = DjangoModelReader
            data_cache_enabled = False
            model = MyModel
            exclude = ('timezone', 'pvmodule')

        def __prepare_data__(self):
            pass

    django_data2 = DjangoSrcTest2(MYMODEL)
    django_data2_parameters = getattr(django_data2, DataSourceBase._param_attr)
    assert isinstance(django_data2, DataSource)
    LOGGER.debug('latitude = %s', django_data2['latitude'])
    assert django_data2['latitude'].magnitude == LAT
    assert django_data2['latitude'].units == UREG.degree
    LOGGER.debug('longitude = %s', django_data2['longitude'])
    assert django_data2['longitude'].magnitude == LON
    assert django_data2['longitude'].units == UREG.degree
    assert 'air_temp' in django_data2_parameters
    assert 'timezone' not in django_data2_parameters
    assert 'pvmodule' not in django_data2_parameters

    class DjangoSrcTest3(DataSource):
        """
        Data source from Django model with all fields.
        """

        class Meta:
            data_reader = DjangoModelReader
            data_cache_enabled = False
            model = MyModel

        def __prepare_data__(self):
            pass

    django_data3 = DjangoSrcTest3(MYMODEL)
    django_data3_parameters = getattr(django_data3, DataSourceBase._param_attr)
    assert isinstance(django_data3, DataSource)
    assert 'air_temp' in django_data3_parameters
    assert 'latitude' in django_data3_parameters
    assert 'longitude' in django_data3_parameters
    assert 'timezone' in django_data3_parameters
    assert 'pvmodule' in django_data3_parameters


def test_hdf5_reader():
    """
    Test :class:`carousel.contrib.readers.HDF5Reader`

    :return: readers and data
    """
    setup_hdf5_test_data()
    # test 1: load data from hdf5 dataset array by node
    params = {
        'GHI': {'units': 'W/m**2', 'extras': {'node': '/data/GHI'}},
        'DNI': {'units': 'W/m**2', 'extras': {'node': '/data/DNI'}},
        'Tdry': {'units': 'degC', 'extras': {'node': '/data/Tdry'}}
    }
    reader1 = HDF5Reader(params)
    assert isinstance(reader1, DataReader)
    data1 = reader1.load_data(H5TEST1)
    assert np.allclose(data1['GHI'], H5TABLE['GlobalHorizontalRadiation'])
    assert data1['GHI'].units == UREG('W/m**2')
    assert np.allclose(data1['DNI'], H5TABLE['DirectNormalRadiation'])
    assert data1['DNI'].units == UREG('W/m**2')
    assert np.allclose(data1['Tdry'], H5TABLE['DryBulbTemperature'])
    assert data1['Tdry'].units == UREG.degC
    # test 2: load data from hdf5 dataset table by node and member name
    params['GHI']['extras']['node'] = 'data'
    params['GHI']['extras']['member'] = 'GlobalHorizontalRadiation'
    params['DNI']['extras']['node'] = 'data'
    params['DNI']['extras']['member'] = 'DirectNormalRadiation'
    params['Tdry']['extras']['node'] = 'data'
    params['Tdry']['extras']['member'] = 'DryBulbTemperature'
    reader2 = HDF5Reader(params)
    assert isinstance(reader1, DataReader)
    data2 = reader2.load_data(H5TEST2)
    assert np.allclose(data2['GHI'], H5TABLE['GlobalHorizontalRadiation'])
    assert data1['GHI'].units == UREG('W/m**2')
    assert np.allclose(data2['DNI'], H5TABLE['DirectNormalRadiation'])
    assert data1['DNI'].units == UREG('W/m**2')
    assert np.allclose(data2['Tdry'], H5TABLE['DryBulbTemperature'])
    assert data1['Tdry'].units == UREG.degC
    teardown_hdf5_test_data()
    return reader1, data1, reader2, data2


if __name__ == '__main__':
    ar, d1 = test_arg_reader()
    a = test_arg_data_src()
    dr, d2 = test_django_reader()
    test_django_data_src()
    h5r1, h5d1, h5r2, h5d2 = test_hdf5_reader()
