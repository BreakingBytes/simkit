"""
Test Carousel core.
"""

from carousel.core import Q_, UREG, Parameter
from nose.tools import eq_, ok_


def test_pv_context():
    """
    Test Pint PV context - specifically suns to power flux and v.v.
    """
    esun = Q_(876.5, UREG.W / UREG.m / UREG.m)
    eq_(esun.to('suns', 'pv'), 0.8765 * UREG.suns)
    esun = Q_(0.8765, UREG.suns)
    ok_(esun.dimensionless)
    eq_(esun.to('W / m ** 2', 'pv'), 876.5 * UREG.W / UREG.m / UREG.m)


def test_fields():
    """
    Test that Carousel field creates an object with attributes
    """
    Parameter._attrs = ['units', 'isconstant']
    test_field = Parameter('my test field', units='W/m**2', isconstant=True)
    ok_(isinstance(test_field, Parameter))
    eq_(test_field['units'], 'W/m**2')
    return test_field
