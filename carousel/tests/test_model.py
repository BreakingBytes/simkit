"""
test model
"""


from nose.tools import ok_, eq_
from carousel.core.models import Model
from carousel.tests import PROJ_PATH, sandia_performance_model, logging
import os

LOGGER = logging.getLogger(__name__)
MODELFILE = 'sandia_performance_model-Tuscon.json'


def test_carousel_model():
    """
    Test Model instantiation methods.
    """
    # test no model and state is 'uninitialized'
    no_model = Model()
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


class PVPowerSAPM1(Model):
    """
    Model JSON parameter file specified as class attributes.
    """
    modelpath = PROJ_PATH
    modelfile = MODELFILE


class PVPowerSAPM2(Model):
    """
    Model layers parameters specified as class attributes.
    """
    modelpath = PROJ_PATH
    outputs = {
        "PVPowerOutputs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "PerformanceOutputs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "IrradianceOutputs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        }
    }
    formulas = {
        "UtilityFormulas": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "PerformanceFormulas": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "IrradianceFormulas": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        }
    }
    data = {
        "PVPowerData": {
            "module": ".sandia_performance_model",
            "package": "pvpower",
            "filename": "Tuscon.json",
            "path": None
        }
    }
    calculations = {
        "UtilityCalcs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "PerformanceCalcs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "IrradianceCalcs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        }
    }
    simulations = {
        "Standalone": {
            "module": ".sandia_performance_model",
            "package": "pvpower",
            "filename": "Tuscon.json",
            "path": "Standalone"
        }
    }


class PVPowerSAPM3(Model):
    """
    Model layer classes specified as class attributes.
    """
    modelpath = PROJ_PATH
    outputs = [
        sandia_performance_model.PVPowerOutputs,
        sandia_performance_model.PerformanceOutputs,
        sandia_performance_model.IrradianceOutputs
    ]
    formulas = [
        sandia_performance_model.UtilityFormulas,
        sandia_performance_model.PerformanceFormulas,
        sandia_performance_model.IrradianceFormulas
    ]
    data = [
        (sandia_performance_model.PVPowerData,
         {"path": None, "filename": "Tuscon.json"})
    ]
    calculations = [
        sandia_performance_model.UtilityCalcs,
        sandia_performance_model.PerformanceCalcs,
        sandia_performance_model.IrradianceCalcs
    ]
    simulations = [
        (sandia_performance_model.Standalone,
         {"path": "Standalone", "filename": "Tuscon.json"})
    ]


class PVPowerSAPM4(Model):
    """
    Even though no data specified, model should still load.
    """
    modelpath = PROJ_PATH
    outputs = [
        sandia_performance_model.PVPowerOutputs,
        sandia_performance_model.PerformanceOutputs,
        sandia_performance_model.IrradianceOutputs
    ]
    formulas = [
        sandia_performance_model.UtilityFormulas,
        sandia_performance_model.PerformanceFormulas,
        sandia_performance_model.IrradianceFormulas
    ]
    data = [sandia_performance_model.PVPowerData]
    calculations = [
        sandia_performance_model.UtilityCalcs,
        sandia_performance_model.PerformanceCalcs,
        sandia_performance_model.IrradianceCalcs
    ]
    simulations = [
        (sandia_performance_model.Standalone,
         {"path": "Standalone", "filename": "Tuscon.json"})
    ]


if __name__ == '__main__':
    m1 = PVPowerSAPM1()
    m2 = PVPowerSAPM2()
    m3 = PVPowerSAPM3()
    m4 = PVPowerSAPM4()
