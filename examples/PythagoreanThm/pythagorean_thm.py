#! python

from carousel.core.data_sources import DataSource, DataParameter
from carousel.core.outputs import Output, OutputParameter
from carousel.core.formulas import Formula, FormulaParameter
from carousel.core.calculations import Calc, CalcParameter
from carousel.core.simulations import Simulation, SimParameter
from carousel.core.models import Model, ModelParameter
from carousel.contrib.readers import ArgumentReader
from carousel.core import UREG
import numpy as np
import os

DATA = {'PythagoreanData': {'adjacent_side': 3.0, 'opposite_side': 4.0}}


class PythagoreanData(DataSource):
    adjacent_side = DataParameter(units='cm', uncertainty=1.0)
    opposite_side = DataParameter(units='cm', uncertainty=1.0)

    def __prepare_data__(self):
        for k, v in self.parameters.iteritems():
            self.uncertainty[k] = {k: v['uncertainty'] * UREG.percent}

    class Meta:
        data_cache_enabled = False
        data_reader = ArgumentReader


class PythagoreanOutput(Output):
    hypotenuse = OutputParameter(units='cm')


def f_pythagorean(a, b):
    a, b = np.atleast_1d(a), np.atleast_1d(b)
    return np.sqrt(a * a + b * b).reshape(1, -1)


class PythagoreanFormula(Formula):
    f_pythagorean = FormulaParameter(
        units=[('=A', ), ('=A', '=A')],
        isconstant=[]
    )

    class Meta:
        module = __name__


class PythagoreanCalc(Calc):
    pythagorean_thm = CalcParameter(
        formula='f_pythagorean',
        args={'data': {'a': 'adjacent_side', 'b': 'opposite_side'}},
        returns=['hypotenuse']
    )


class PythagoreanSim(Simulation):
    settings = SimParameter(
        ID='Pythagorean Theorem',
        commands=['start', 'load', 'run'],
        sim_length=[0, 'hour'],
        write_fields={
            'data': ['adjacent_side', 'opposite_side'],
            'outputs': ['hypotenuse']
        }
    )


class PythagoreanModel(Model):
    data = ModelParameter(sources=[PythagoreanData])
    outputs = ModelParameter(sources=[PythagoreanOutput])
    formulas = ModelParameter(sources=[PythagoreanFormula])
    calculations = ModelParameter(sources=[PythagoreanCalc])
    simulations = ModelParameter(sources=[PythagoreanSim])

    class Meta:
        modelpath = os.path.dirname(__file__)


if __name__ == '__main__':
    m = PythagoreanModel()
    m.command('run', data=DATA)
    out_reg = m.registries['outputs']
    fmt = {
        'output': out_reg['hypotenuse'],
        'uncertainty': out_reg.uncertainty['hypotenuse']['hypotenuse']
    }
    print 'hypotenuse = %(output)s +/- %(uncertainty)s' % fmt
