"""
test model
"""


from nose.tools import ok_, eq_
from carousel.core.models import Model, ModelParameter
from carousel.tests import PROJ_PATH, sandia_performance_model, logging
import os

LOGGER = logging.getLogger(__name__)
MODELFILE = 'sandia_performance_model-Tuscon.json'


def test_carousel_model():
    """
    Test Model instantiation methods.
    """
    # test no model and state is 'uninitialized'
    no_model = PVPowerSAPM0()
    ok_(isinstance(no_model, Model))
    eq_(no_model.state, 'uninitialized')
    # instantiate model by passing JSON parameter file
    model_test_file = os.path.join(PROJ_PATH, 'models', MODELFILE)
    carousel_model_test0 = sandia_performance_model.SAPM(model_test_file)
    ok_(isinstance(carousel_model_test0, Model))
    # path to JSON parameter file specified as class attributes
    carousel_model_test1 = PVPowerSAPM1()
    ok_(isinstance(carousel_model_test1, Model))
    # layers defined as class attributes directly in model class definition
    carousel_model_test2 = PVPowerSAPM2()
    ok_(isinstance(carousel_model_test2, Model))
    # layer classes specified as class attributes
    carousel_model_test3 = PVPowerSAPM3()
    ok_(isinstance(carousel_model_test3, Model))
    # same as test #3 but no data files are specified
    carousel_model_test4 = PVPowerSAPM4()
    ok_(isinstance(carousel_model_test4, Model))
    carousel_model_test4_data = getattr(carousel_model_test4, 'data')
    carousel_model_test4_data.open(
        'PVPowerData', 'Tuscon.json', 'data', PROJ_PATH
    )


class PVPowerSAPM0(Model):
    """
    Model that can't be initialized.
    """


class PVPowerSAPM1(Model):
    """
    Model JSON parameter file specified as class attributes.
    """
    class Meta:
        modelpath = PROJ_PATH
        modelfile = os.path.join('models', MODELFILE)


class PVPowerSAPM2(Model):
    """
    Model layers parameters specified as class attributes.
    """
    outputs = ModelParameter(
        layer='Outputs',
        sources=["PVPowerOutputs", "PerformanceOutputs", "IrradianceOutputs"],
        module=".sandia_performance_model",
        package="pvpower"
    )
    formulas = ModelParameter(
        layer='Formulas',
        sources=[
            "UtilityFormulas", "PerformanceFormulas", "IrradianceFormulas"
        ],
        module=".sandia_performance_model",
        package="pvpower"
    )
    data = ModelParameter(
        layer='Data',
        sources=[("PVPowerData", {"filename": "Tuscon.json", "path": None})],
        module=".sandia_performance_model",
        package="pvpower"
    )
    calculations = ModelParameter(
        layer='Calculations',
        sources=["UtilityCalcs", "PerformanceCalcs", "IrradianceCalcs"],
        module=".sandia_performance_model",
        package="pvpower"
    )
    simulations = ModelParameter(
        layer="Simulations",
        sources=[
            ("Standalone", {"filename": "Tuscon.json", "path": "Standalone"})
        ],
        module=".sandia_performance_model",
        package="pvpower"
    )

    class Meta:
        modelpath = PROJ_PATH


class PVPowerSAPM3(Model):
    """
    Model layer classes specified as class attributes.
    """
    outputs = ModelParameter(
        layer='Outputs',
        sources=[
            sandia_performance_model.PVPowerOutputs,
            sandia_performance_model.PerformanceOutputs,
            sandia_performance_model.IrradianceOutputs
        ]
    )
    formulas = ModelParameter(
        layer='Formulas',
        sources=[
            sandia_performance_model.UtilityFormulas,
            sandia_performance_model.PerformanceFormulas,
            sandia_performance_model.IrradianceFormulas
        ]
    )
    data = ModelParameter(
        layer='Data',
        sources=[(sandia_performance_model.PVPowerData,
                  {"path": None, "filename": "Tuscon.json"})]
    )
    calculations = ModelParameter(
        layer='Calculations',
        sources=[
            sandia_performance_model.UtilityCalcs,
            sandia_performance_model.PerformanceCalcs,
            sandia_performance_model.IrradianceCalcs
        ]
    )
    simulations = ModelParameter(
        layer="Simulations",
        sources=[(sandia_performance_model.Standalone,
                  {"path": "Standalone", "filename": "Tuscon.json"})]
    )

    class Meta:
        modelpath = PROJ_PATH


class PVPowerSAPM4(Model):
    """
    Even though no data specified, model should still load.
    """
    outputs = ModelParameter(
        layer='Outputs',
        sources=[
            sandia_performance_model.PVPowerOutputs,
            sandia_performance_model.PerformanceOutputs,
            sandia_performance_model.IrradianceOutputs
        ]
    )
    formulas = ModelParameter(
        layer='Formulas',
        sources=[
            sandia_performance_model.UtilityFormulas,
            sandia_performance_model.PerformanceFormulas,
            sandia_performance_model.IrradianceFormulas
        ]
    )
    data = ModelParameter(
        layer='Data',
        sources=[sandia_performance_model.PVPowerData]
    )
    calculations = ModelParameter(
        layer='Calculations',
        sources=[
            sandia_performance_model.UtilityCalcs,
            sandia_performance_model.PerformanceCalcs,
            sandia_performance_model.IrradianceCalcs
        ]
    )
    simulations = ModelParameter(
        layer="Simulations",
        sources=[(sandia_performance_model.Standalone,
                  {"path": "Standalone", "filename": "Tuscon.json"})]
    )

    class Meta:
        modelpath = PROJ_PATH


if __name__ == '__main__':
    test_carousel_model()
