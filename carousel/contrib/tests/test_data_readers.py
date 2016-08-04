"""
Test contrib data readers.
"""

from carousel.contrib.readers import (
    ArgumentReader, DjangoModelReader, HDF5Reader
)
from carousel.core.data_sources import DataSource
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
    [(0L, 0L, 15.200897216796875), (0L, 0L, 14.545711517333984),
     (0L, 0L, 13.890524864196777), (0L, 0L, 13.540611267089844),
     (0L, 0L, 13.190696716308594), (0L, 0L, 12.942743301391602),
     (0L, 0L, 12.904003143310547), (115L, 566L, 14.073929786682129),
     (329L, 809L, 15.947802543640137), (558L, 936L, 18.07691764831543),
     (750L, 780L, 20.15163803100586), (500L, 197L, 20.636459350585938),
     (510L, 147L, 21.00153350830078), (531L, 139L, 21.318157196044922),
     (486L, 120L, 21.44940757751465), (437L, 130L, 21.36214256286621),
     (311L, 80L, 21.034954071044922), (259L, 131L, 20.530967712402344),
     (124L, 106L, 19.722484588623047), (4L, 0L, 18.716384887695312),
     (0L, 0L, 17.36248207092285), (0L, 0L, 16.008577346801758),
     (0L, 0L, 14.654674530029297), (0L, 0L, 13.30077075958252)],
    dtype=H5DTYPE
)
H5DATA = np.concatenate(
    [H5TABLE[col].reshape(-1, 1) for col in H5TABLE.dtype.names], axis=1
)
with h5py.File(H5TEST1, 'w') as h5f:
    h5f.create_group('group')
    h5f['group'].create_dataset('data', data=H5DATA)
with h5py.File(H5TEST2, 'w') as h5f:
    h5f.create_group('group')
    h5f['group'].create_dataset('data', data=H5TABLE)


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
    Django model for testing :class:`~carousel.contrib.readers.DjangoModelReader`.
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
    Test :class:`~carousel.contrib.readers.ArgumentReader` is instantiated and can
    load argument data units and values correctly.

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
        'pvmodule': {'argpos': 0},
        'air_temp': {'units': 'celsius', 'argpos': 1},
        'latitude': {'units': 'degrees'},
        'longitude': {'units': 'degrees'},
        'timezone': {'units': 'hours'}
    }
    arg_reader = ArgumentReader(parameters)
    assert isinstance(arg_reader, ArgumentReader)  # instance of ArgumentReader
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
        data_reader = ArgumentReader
        data_cache_enabled = False
        air_temp = {'units': 'celsius', 'argpos': 0}
        latitude = {'units': 'degrees', 'isconstant': True}
        longitude = {'units': 'degrees', 'isconstant': True}
        timezone = {'units': 'hours'}

        def __prepare_data__(self):
            pass

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
    Test :class:`~carousel.contrib.readers.DjangoModelReader` is instantiated and
    can load argument data units and values correctly.

    :return: django reader and data
    :raises: AssertionError
    """
    params = {'air_temp': {'units': 'celsius'}}
    meta = type('Meta', (), {'model': MyModel})
    django_reader = DjangoModelReader(params, meta)
    assert isinstance(django_reader, DjangoModelReader)
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
        data_reader = DjangoModelReader
        data_cache_enabled = False
        # parameters
        air_temp = {'units': 'celsius'}
        latitude = {'units': 'degrees'}
        longitude = {'units': 'degrees'}

        class Meta:
            model = MyModel
            fields = ('air_temp', 'latitude', 'longitude')

        def __prepare_data__(self):
            pass

    django_data1 = DjangoSrcTest1(MYMODEL)
    assert isinstance(django_data1, DjangoSrcTest1)
    LOGGER.debug('air temp = %s', django_data1['air_temp'])
    assert django_data1['air_temp'].magnitude == TAIR
    assert django_data1['air_temp'].units == UREG.celsius
    assert 'latitude' in django_data1.parameters
    assert 'longitude' in django_data1.parameters
    assert 'timezone' not in django_data1.parameters
    assert 'pvmodule' not in django_data1.parameters

    class DjangoSrcTest2(DataSource):
        """
        Data source from Django model that excludes fields.
        """
        data_reader = DjangoModelReader
        data_cache_enabled = False
        # parameters
        air_temp = {'units': 'celsius'}
        latitude = {'units': 'degrees'}
        longitude = {'units': 'degrees'}

        class Meta:
            model = MyModel
            exclude = ('timezone', 'pvmodule')

        def __prepare_data__(self):
            pass

    django_data2 = DjangoSrcTest2(MYMODEL)
    assert isinstance(django_data2, DjangoSrcTest2)
    LOGGER.debug('latitude = %s', django_data2['latitude'])
    assert django_data2['latitude'].magnitude == LAT
    assert django_data2['latitude'].units == UREG.degree
    LOGGER.debug('longitude = %s', django_data2['longitude'])
    assert django_data2['longitude'].magnitude == LON
    assert django_data2['longitude'].units == UREG.degree
    assert 'air_temp' in django_data2.parameters
    assert 'timezone' not in django_data2.parameters
    assert 'pvmodule' not in django_data2.parameters

    class DjangoSrcTest3(DataSource):
        """
        Data source from Django model with all fields.
        """
        data_reader = DjangoModelReader
        data_cache_enabled = False

        class Meta:
            model = MyModel

        def __prepare_data__(self):
            pass

    django_data3 = DjangoSrcTest3(MYMODEL)
    assert isinstance(django_data3, DjangoSrcTest3)
    assert 'air_temp' in django_data3.parameters
    assert 'latitude' in django_data3.parameters
    assert 'longitude' in django_data3.parameters
    assert 'timezone' in django_data3.parameters
    assert 'pvmodule' in django_data3.parameters
