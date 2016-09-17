"""
test model
"""


from nose.tools import ok_
from carousel.core.models import Model, BasicModel
from carousel.tests import PROJ_PATH, pvpower_models, logging
import os

LOGGER = logging.getLogger(__name__)


def test_carousel_model():
    """
    Test Model instantiation.
    """

    model_test_file = os.path.join(PROJ_PATH, 'models',
                                   'sandia_performance_model-Tuscon.json')
    carousel_model_test1 = pvpower_models.SAPM(model_test_file)
    ok_(isinstance(carousel_model_test1, Model))

    class PVPowerSAPM(BasicModel):
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

    carousel_model_test2 = PVPowerSAPM()
    ok_(isinstance(carousel_model_test2, Model))
