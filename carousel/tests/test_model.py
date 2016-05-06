"""
test model
"""


from nose.tools import ok_
from carousel.core.models import Model
from carousel.tests import PROJ_PATH, pvpower_models, logging
import os

LOGGER = logging.getLogger(__name__)


def test_carousel_model():
    """
    Test Model
    """

    test_model_file = os.path.join(PROJ_PATH, 'models',
                                   'sandia_performance_model-Tuscon.json')
    carousel_model_test1 = pvpower_models.SAPM(test_model_file)
    ok_(isinstance(carousel_model_test1, Model))
