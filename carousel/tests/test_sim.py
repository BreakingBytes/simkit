"""
Simulation tests.
"""

from carousel.core import logging, UREG
from carousel.core.models import Model, ModelParameter
from carousel.core.data_sources import DataParameter, DataSource
from carousel.core.formulas import FormulaParameter, Formula
from carousel.core.simulations import SimParameter, Simulation
from carousel.core.outputs import OutputParameter, Output
from carousel.core.calculations import Calc, CalcParameter
from carousel.contrib.readers import ArgumentReader
from carousel.tests import PROJ_PATH
import numpy as np
import os
import sympy

LOGGER = logging.getLogger(__name__)


def test_make_sim_metaclass():
    """
    Test setting the simulation parameter file as class attributes versus
    specifying the simulation parameter file in the model parameter file.

    :return: simulation
    """

    class SimTest1(Simulation):
        class Meta:
            sim_file = 'Tuscon.json'
            sim_path = os.path.join(PROJ_PATH, 'simulations', 'Standalone')

    sim_test1 = SimTest1()
    return sim_test1


class PythagorasData(DataSource):
    a = DataParameter(**{'units': 'cm', 'argpos': 0})
    b = DataParameter(**{'units': 'cm', 'argpos': 2})
    a_unc = DataParameter(**{'units': 'cm', 'argpos': 1})
    b_unc = DataParameter(**{'units': 'cm', 'argpos': 3})

    class Meta:
        data_cache_enabled = False
        data_reader = ArgumentReader

    def __prepare_data__(self):
        keys = list(self.parameters.keys())
        for k in keys:
            if k.endswith('_unc'):
                unc = self.data.pop(k)
                self.data_source.pop(k)
                kunc = k[:-4]
                v = self.data[kunc]
                if not unc.dimensionless:
                    unc = (unc / v)
                # raises dimensionality error if not dimensionless
                self.uncertainty[kunc] = {kunc: unc.to(UREG.percent)}
            else:
                self.isconstant[k] = True


class PythagorasOutput(Output):
    c = OutputParameter(**{'units': 'cm', 'isconstant': True})


def f_hypotenuse(a, b):
    a, b = np.atleast_1d(a), np.atleast_1d(b)
    return np.sqrt(a * a + b * b).reshape(1, -1)


class PythagorasFormula(Formula):
    f_hypotenuse = FormulaParameter(
        args=['a', 'b'],
        units=[('=A', ), ('=A', '=A')],
        isconstant=[]
    )

    class Meta:
        module = 'carousel.tests.test_sim'


class PythagorasCalc(Calc):
    pythagorean_thm = CalcParameter(
        is_dynamic=False,
        formula='f_hypotenuse',
        args={'data': {'a': 'a', 'b': 'b'}},
        returns=['c']
    )


class PythagorasSim(Simulation):
    settings = SimParameter(
        ID='Pythagorean Theorem',
        commands=['start', 'load', 'run', 'pause'],
        path='~/Carousel_Tests',
        thresholds=None,
        interval=[1, 'hour'],
        sim_length=[0, 'hour'],
        write_frequency=1,
        write_fields={'data': ['a', 'b'], 'outputs': ['c']},
        display_frequency=1,
        display_fields={'data': ['a', 'b'], 'outputs': ['c']},
    )


class PythagorasModel(Model):
    data = ModelParameter(sources=[PythagorasData])
    outputs = ModelParameter(sources=[PythagorasOutput])
    formulas = ModelParameter(sources=[PythagorasFormula])
    calculations = ModelParameter(sources=[PythagorasCalc])
    simulations = ModelParameter(sources=[PythagorasSim])

    class Meta:
        modelpath = os.path.dirname(__file__)


def test_call_sim_with_args():
    a, a_unc, b, b_unc = 3.0, 0.1, 4.0, 0.1
    c = f_hypotenuse(a, b)
    m1 = PythagorasModel()
    data = {'PythagorasData': {'a': a, 'b': b, 'a_unc': a_unc, 'b_unc': b_unc}}
    m1.command('run', data=data)
    assert m1.registries['outputs']['c'].m == c
    assert m1.registries['outputs']['c'].u == UREG.cm
    x, y = sympy.symbols('x, y')
    z = sympy.sqrt(x * x + y * y)
    fx = sympy.lambdify((x, y), z.diff(x))
    fy = sympy.lambdify((x, y), z.diff(y))
    dz = np.sqrt(fx(a, b) ** 2 * a_unc ** 2 + fy(a, b) ** 2 * b_unc ** 2)
    c_unc = c * np.sqrt(m1.registries['outputs'].variance['c']['c'])
    LOGGER.debug('uncertainty in c is %g', c_unc)
    assert np.isclose(dz, c_unc.item())
    c_unc = c * m1.registries['outputs'].uncertainty['c']['c'].to('fraction')
    assert np.isclose(dz, c_unc.m.item())
    return m1


if __name__ == '__main__':
    m = test_call_sim_with_args()
