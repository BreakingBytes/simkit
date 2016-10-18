"""
Simulation tests.
"""

from carousel.core import (
    logging, data_sources, outputs, formulas, calculations, simulations, models,
    UREG
)
from carousel.core.data_sources import DataParameter
from carousel.core.formulas import FormulaParameter
from carousel.core.simulations import SimParameter
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

    class SimTest1(simulations.Simulation):
        sim_file = 'Tuscon.json'
        sim_path = os.path.join(PROJ_PATH, 'simulations', 'Standalone')

    sim_test1 = SimTest1()
    return sim_test1


class PythagorasData(data_sources.DataSource):
    data_cache_enabled = False
    data_reader = ArgumentReader
    a = DataParameter(**{'units': 'cm', 'argpos': 0})
    b = DataParameter(**{'units': 'cm', 'argpos': 2})
    a_unc = DataParameter(**{'units': 'cm', 'argpos': 1})
    b_unc = DataParameter(**{'units': 'cm', 'argpos': 3})

    def __prepare_data__(self):
        keys = self.parameters.keys()
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


class PythagorasOutput(outputs.Output):
    c = {'units': 'cm', 'isconstant': True}


def f_hypotenuse(a, b):
    a, b = np.atleast_1d(a), np.atleast_1d(b)
    return np.sqrt(a * a + b * b).reshape(1, -1)


class PythagorasFormula(formulas.Formula):
    f_hypotenuse = FormulaParameter(
        args=['a', 'b'],
        units=[('=A', ), ('=A', '=A')],
        isconstant=[]
    )

    class Meta:
        module = 'carousel.tests.test_sim'


class PythagorasCalc(calculations.Calc):
    static = [{
        'formula': 'f_hypotenuse',
        'args': {'data': {'a': 'a', 'b': 'b'}},
        'returns': ['c']
    }]


class PythagorasSim(simulations.Simulation):
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


class PythagorasModel(models.Model):
    modelpath = os.path.dirname(__file__)
    data = [PythagorasData]
    outputs = [PythagorasOutput]
    formulas = [PythagorasFormula]
    calculations = [PythagorasCalc]
    simulations = [PythagorasSim]


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
    assert np.isclose(dz, np.array(c_unc))
    c_unc = c * m1.registries['outputs'].uncertainty['c']['c']
    assert np.isclose(dz, np.array(c_unc))
    return m1


if __name__ == '__main__':
    m = test_call_sim_with_args()
