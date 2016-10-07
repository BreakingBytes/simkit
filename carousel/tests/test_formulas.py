"""
test formulas
"""

from nose.tools import ok_, eq_
import numpy as np
from carousel.core import UREG
from carousel.core.formulas import Formula, NumericalExpressionImporter
from carousel.tests import PROJ_PATH
import os


def test_formulas_metaclass():
    """
    Test Formulas
    """

    class FormulaTest1(Formula):
        formulas_file = 'utils.json'
        formulas_path = os.path.join(PROJ_PATH, 'formulas')

    formulas_test1 = FormulaTest1()
    ok_(isinstance(formulas_test1, Formula))
    eq_(formulas_test1.param_file,
        os.path.join(PROJ_PATH, 'formulas', 'utils.json'))

    class FormulaTest2(Formula):
        module = ".utils"
        package = "formulas"
        formulas = {
            "f_daterange": None,
            "f_energy": {
                "args": ["ac_power", "times"],
                "units": [["watt_hour", None], ["W", None]]
            },
            "f_rollup": {
                "args": ["items", "times", "freq"],
                "units": ["=A", ["=A", None, None]]
            }
        }

    formulas_test2 = FormulaTest2()
    ok_(isinstance(formulas_test2, Formula))
    for k, v in formulas_test2.parameters.iteritems():
        eq_(formulas_test1.parameters[k], v)


def test_numexpr_formula():
    """
    Test formulas imported using ``numexpr``
    """

    class NumexprFormula(Formula):
        formula_importer = NumericalExpressionImporter
        formulas = {
            'f_hypotenuse': {
                'expression': 'sqrt(a * a + b * b)',
                'args': ['a', 'b'],
                'units': [('=A', ), ('=A', '=A')],
                'isconstant': []
            }
        }

    numexpr_formula = NumexprFormula()
    ok_(isinstance(numexpr_formula, Formula))
    unc = 0.1  # uncertainty
    var = unc**2  # variance
    cov = np.array([[[var, 0], [0, var]], [[var, 0], [0, var]]])
    a = [3.0, 12.0] * UREG.cm
    b = [4.0, 5.0] * UREG.cm
    f_hypotenuse = numexpr_formula.formulas['f_hypotenuse']
    c, c_unc, c_jac = f_hypotenuse(a, b, __covariance__=cov)
    assert np.allclose(c.m, np.array([5.0, 13.0]))
    eq_(c.u, UREG.centimeter)
    # import sympy
    # x, y = sympy.symbols('x, y')
    # z = sympy.sqrt(x * x + y * y)
    # fx, fy = z.diff(x), z.diff(y)
    # fx, fy = x/sqrt(x**2 + y**2), y/sqrt(x**2 + y**2)
    # fx, fy = x/z, y/z
    # dz = sqrt(fx**2 * dx**2 + fy**2 * dy**2)
    da, db = a.m * unc, b.m * unc
    fa, fb = a.m / c.m, b.m / c.m
    dc = (fa ** 2 * da ** 2) + (fb ** 2 * db ** 2)
    assert np.allclose(c_unc.squeeze(), dc)
    fc = np.array([fa, fb]).T
    assert np.allclose(c_jac.squeeze(), fc)
    return numexpr_formula


if __name__ == '__main__':
    f = test_numexpr_formula()
