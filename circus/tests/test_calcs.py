"""
test calculations
"""

from nose.tools import ok_, eq_
from circus.core.calculation import Calc
from circus.tests import PROJ_PATH
import os


# def test_calc_metaclass():
#     """
#     test calculation class is created with params file using metaclass
#     """
#
#     class CalcTest1(Calc):
#         calcs_file = 'pvpower.json'
#         calcs_path = os.path.join(PROJ_PATH, 'calculations')
#
#     calc_test1 = CalcTest1()
#     ok_(isinstance(calc_test1, Calc))
#     eq_(calc_test1.param_file,
#         os.path.join(PROJ_PATH, 'calculations', 'pvpower.json'))
