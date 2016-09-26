"""
Simulation tests.
"""

from carousel.core import (
    data_sources, outputs, formulas, calculations, simulations, models, UREG
)
from carousel.contrib.readers import ArgumentReader
from carousel.tests import PROJ_PATH
import numpy as np
import os


def test_make_sim_metaclass():

    class SimTest1(simulations.Simulation):
        sim_file = 'Tuscon.json'
        sim_path = os.path.join(PROJ_PATH, 'simulations', 'Standalone')

    sim_test1 = SimTest1()


class PythagorasData(data_sources.DataSource):
    data_cache_enabled = False
    data_reader = ArgumentReader
    a = {'units': 'cm'}
    b = {'units': 'cm'}
    a_unc = {'units': 'cm'}
    b_unc = {'units': 'cm'}

    def __prepare_data__(self):
        keys = self.parameters.keys()
        for k in keys:
            self.isconstant[k] = True
            if k.endswith('_unc'):
                unc = self.data.pop(k)
                v = self.data[k[:-4]]
                if not unc.dimensionless:
                    unc = (unc / v)
                # raises dimensionality error if not dimensionless
                self.uncertainty[k] = {k: unc.to(UREG.percent)}


class PythagorasOutput(outputs.Output):
    c = {'units': 'cm', 'isconstant': True}


def f_hypotenuse(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return np.sqrt(a * a + b * b)


class PythagorasFormula(formulas.Formula):
    module = 'carousel.tests.test_sim'
    formulas = {
        'f_hypotenuse': {
            'args': ['a', 'b'], 'units': [('=A', ), ('=A', '=A', None, None)]
        }
    }


class PythagorasCalc(calculations.Calc):
    static = [{
        'formula': 'f_hypotenuse',
        'args': {'data': {'a': 'a', 'b': 'b'}},
        'returns': ['c']
    }]


class PythagorasSim(simulations.Simulation):
    ID = 'Pythagoras Asynchronous Batch Simulation'
    commands = ['start', 'load', 'run', 'pause']
    path = '~/Carousel/Tests'
    thresholds = None
    interval_length = 1 * UREG.hour
    simulation_length = 0 * UREG.hour
    write_frequency = 1
    write_fields = {'data': ['a', 'b'], 'outputs': ['c']}
    display_frequency = 1
    display_fields = {'data': ['a', 'b'], 'outputs': ['c']}
    data = {
        'Tuscon': {
            'PythagorasData': {
                'a': 3, 'b': 4, 'a_unc': 0.1, 'b_unc': 0.1
            }
        },
        'Phoenix': {
            'PythagorasData': {
                'a': 5, 'b': 12, 'a_unc': 0.1, 'b_unc': 0.1
            }
        }
    }


class PythagorasModel(models.Model):
    modelpath = os.path.dirname(__file__)
    data = [PythagorasData]
    outputs = [PythagorasOutput]
    formulas = [PythagorasFormula]
    calculations = [PythagorasCalc]
    simulations = [PythagorasSim]


def test_call_sim_with_args():
    m1 = PythagorasModel()
    m1.command('run')
    return m1


if __name__ == '__main__':
    m1 = test_call_sim_with_args()
