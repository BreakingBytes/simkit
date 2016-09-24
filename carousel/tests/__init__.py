"""
Carousel tests
"""

from carousel.core import logging
import importlib
import os
import sys

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
PROJECT = 'PVPower'
MODEL = 'sandia_performance_model'
TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
PROJ_PATH = os.path.abspath(os.path.join(
    TESTS_DIR, '..', '..', 'examples', PROJECT
))

sys.path.append(PROJ_PATH)
sandia_performance_model = importlib.import_module(
    '.%s' % MODEL, PROJECT.lower()
)
