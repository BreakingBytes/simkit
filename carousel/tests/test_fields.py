"""
Testing field subclasses in different layers.
"""

from carousel.core import Field, UREG
from carousel.core.data_sources import DataSource
from carousel.contrib.readers import ArgumentReader


class VelocityData(DataSource):
    data_reader = ArgumentReader
    data_cache_enabled = False
    Field._attrs = ['units', 'isconstant', 'uncertainty', 'argpos']
    distance = Field(units='m', isconstant=True, uncertainty=0.01, argpos=0)
    elapsed_time = Field(units='s', isconstant=True, uncertainty=0.01, argpos=1)

    def __prepare_data__(self):
        pass


def test_data_with_fields():
    v = VelocityData(distance=96540, elapsed_time=3600)
    assert isinstance(v, DataSource)
    assert v['distance'] == 96540 * UREG.m
    assert v['distance'] == 3600 * UREG.s
    return v


if __name__ == '__main__':
    v = test_data_with_fields()
