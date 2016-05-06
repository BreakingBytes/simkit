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
