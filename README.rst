.. image:: https://travis-ci.org/SunPower/Carousel.svg?branch=master
    :target: https://travis-ci.org/SunPower/Carousel

Carousel - Model Simulation Framework
=====================================
Carousel ia a framework for simulating mathematical models that decouples
the models from the simulation implementation. It takes care of boilerplate
routines such as loading data from various sources into a key store that can be
used from any calculation, determining the correct order of calculations,
stepping through dynamic simulations and generating output reports and
visualizations, so that you can focus on developing models and don't have to
worry about how to add new models or how to integrate changes.

Requirements
------------
* `Pint <http://pint.readthedocs.org/en/latest/>`_
* `NumPy <http://www.numpy.org/>`_
* `h5py <http://www.h5py.org/>`_
* `xlrd <http://www.python-excel.org/>`_
* `UncertaintyWrapper <http://sunpower.github.io/UncertaintyWrapper/>`_

Installation
------------
Carousel `releases are on PyPI <https://pypi.python.org/pypi/Carousel>`_ and on
`GitHub <https://github.com/SunPower/Carousel/releases>`_. You can use either
``pip``, ``conda``, or ``distutils`` to install Carousel.

`pip <https://pip.pypa.io/en/stable/>`_ ::

    $ pip install Carousel

Extract the archive to use `disutils <https://docs.python.org/2/install/>`_ ::

    $ python setup.py install

`SunPower conda channel <https://anaconda.org/sunpower/carousel>`_ ::

    $ conda install -c sunpower Carousel

Documentation
-------------
Carousel `documentation <https://sunpower.github.io/Carousel>`_ is
online. It's also included in the distribution and can be built using
`Sphinx <http://www.sphinx-doc.org/en/stable/>`_ by running the ``Makefile``
found in the ``docs`` folder of the Carousel package. Once built documentation
will be found in the ``_build`` folder under the tree corresponding to the type
of documentation built. *EG*: HTML documentation is in ``docs/_build/html``.

Contributions
-------------
Carousel `source code <https://github.com/SunPower/Carousel>`_ is
online. Fork it and report
`issues <https://github.com/SunPower/Carousel/issues>`_, make suggestions or
create pull requests. Discuss the roadmap or download presentations on the
`wiki <https://github.com/SunPower/Carousel/wiki>`_

History
-------
The
`change log for all releases <https://github.com/SunPower/Carousel/releases>`_
is on GitHub.

Quickstart Example
------------------
Define data, outputs, formulas, calculations, simulations and model::

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

This is the `MCVE <https://stackoverflow.com/help/mcve>`_ of a Carousel model.
