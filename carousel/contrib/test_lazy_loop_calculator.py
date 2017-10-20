#! python

"""
Test the lazy looping calculator
"""

from carousel.core import Registry, UREG
from carousel.core.formulas import FormulaRegistry
from carousel.core.data_sources import DataRegistry
from carousel.core.outputs import OutputRegistry
# from uncertainty_wrapper import unc_wrapper_args
from carousel.contrib.lazy_looping_calculator import (
    reg_copy, LazyLoopingCalculator
)
import numpy as np

PYTHAGOREAN_UNITS = [('=A', ), ('=A', '=A')]


class TestRegistry(Registry):
    """A mock Carousel registry for testing."""
    meta_names = ['testdata']


def test_reg_copy():
    """Test the lazy loop calculator registry copy method."""
    testreg = TestRegistry()
    testreg_data = {'foo': [1, 2, 3], 'bar': [4, 5, 6]}
    testreg_metadata = {'foo': True, 'bar': False}
    testreg.register(testreg_data, testdata=testreg_metadata)
    newreg = reg_copy(testreg, ['foo'])
    assert isinstance(newreg, Registry)
    assert newreg['foo'] == [1, 2, 3]
    assert newreg.testdata['foo'] is True
    assert newreg.get('bar', None) is None
    assert newreg.testdata.get('bar', None) is None
    return newreg


def f_pythagorian_thm(adjacent, opposite):
    """calculate hypotenuse"""
    return np.atleast_1d(np.sqrt(adjacent ** 2 + opposite ** 2))


def test_lazy_loop_calculator_cls():
    """Test the lazy loop calculator class."""
    calc = {'formula': 'pythagorian_thm',
            'args': {'data': {'adjacent': 'a', 'opposite': 'b'}, 'outputs': {}},
            'returns': ['c']}
    formula_reg = FormulaRegistry()
    formula_reg.register(
        {'pythagorian_thm': UREG.wraps(*PYTHAGOREAN_UNITS)(f_pythagorian_thm)},
        args={'pythagorian_thm': ['adjacent', 'opposite']},
        units={'pythagorian_thm': PYTHAGOREAN_UNITS},
        isconstant={'pythagorian_thm': None}
    )
    data_reg = DataRegistry()
    data_reg.register(
        {'a': [3., 5., 7., 9., 11.] * UREG('cm'),
         'b': [4., 12., 24., 40., 60.] * UREG('cm')},
        uncertainty=None,
        variance=None,
        isconstant={'a': True, 'b': True}
    )
    out_reg = OutputRegistry()
    out_reg.register({'c': np.zeros(5) * UREG.m})
    # repeat args are listed as formula names, not data reg names!
    calculator = LazyLoopingCalculator(repeat_args=['adjacent', 'opposite'])
    calculator.calculate(calc, formula_reg, data_reg, out_reg)
    assert np.allclose(out_reg['c'].m, PYTHAGOREAN_TRIPLES)  # check magnitudes
    assert out_reg['c'].u == UREG.m  # output units are meters
    return out_reg


# def test_lazy_loop_calculator_cov():
#     """test lazy loop calculator also works with covariance?"""
#     calc = {'formula': 'pythagorian_thm',
#             'args': {'data': {'adjacent': 'a', 'opposite': 'b'},
#                      'outputs': {}},
#             'returns': ['c']}
#     formula_reg = FormulaRegistry()
#     formula_reg.register(
#         {'pythagorian_thm': UREG.wraps(*PYTHAGOREAN_UNITS)(
#             unc_wrapper_args(0, 1)(f_pythagorian_thm)
#         )},
#         args={'pythagorian_thm': ['adjacent', 'opposite']},
#         units={'pythagorian_thm': PYTHAGOREAN_UNITS},
#         isconstant={'pythagorian_thm': []}
#     )
#     data_reg = DataRegistry()
#     data_reg.register(
#         {'a': [3., 5., 7., 9., 11.] * UREG('cm'),
#          'b': [4., 12., 24., 40., 60.] * UREG('cm')},
#         uncertainty={'a': {'a': 1.*UREG.percent},
#                      'b': {'b': 1.*UREG.percent}},
#         variance={'a': {'a': 0.0001}, 'b': {'b': 0.0001}},
#         isconstant={'a': True, 'b': True}
#     )
#     out_reg = OutputRegistry()
#     out_reg.register({'c': np.zeros(5) * UREG.m})
#     calculator = LazyLoopingCalculator(repeat_args=['adjacent', 'opposite'])
#     calculator.calculate(calc, formula_reg, data_reg, out_reg)
#     assert np.allclose(out_reg['c'].m, PYTHAGOREAN_TRIPLES)
#     return out_reg


PYTHAGOREAN_TRIPLES = [0.05, 0.13, 0.25, 0.41, 0.61]  # hypotenuse in meters

if __name__ == '__main__':
    NEWREG = test_reg_copy()
