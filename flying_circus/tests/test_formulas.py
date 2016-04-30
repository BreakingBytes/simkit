"""
test formulas
"""

from nose.tools import ok_, eq_
from flying_circus.core.formulas import Formula
from flying_circus.tests import PROJ_PATH
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
            "f_daterange": {"islinear": True},
            "f_energy": {"islinear": True},
            "f_rollup": {"islinear": True}
        }

    formulas_test2 = FormulaTest2()
    ok_(isinstance(formulas_test2, Formula))
    for k, v in formulas_test2.parameters.iteritems():
        eq_(formulas_test1.parameters[k], v)
