"""
Testing field subclasses in different layers.
"""

from carousel.core import UREG, Parameter
from carousel.core.data_sources import DataSource, DataParameter
from carousel.contrib.readers import ArgumentReader


class VelocityData(DataSource):
    data_reader = ArgumentReader
    data_cache_enabled = False
    distance = DataParameter(units='m', isconstant=True, uncertainty=0.01,
                             argpos=0)
    elapsed_time = DataParameter(units='s', isconstant=True, uncertainty=0.01,
                                 argpos=1)

    def __prepare_data__(self):
        pass


def test_data_with_fields():
    d, t = 96540, 3600
    dk, tk = 'distance', 'elapsed_time'
    v = VelocityData(distance=d, elapsed_time=t)
    assert isinstance(v, DataSource)
    assert isinstance(v.parameters[dk], Parameter)
    assert isinstance(v.parameters[tk], Parameter)
    assert v[dk] == d * UREG.m
    assert v[tk] == t * UREG.s
    return v


if __name__ == '__main__':
    velocity = test_data_with_fields()
