"""
SimKit tests
"""

from simkit.core import logging
import importlib
import os
import sys

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
PROJECT = 'PVPower'
MODEL = 'sandia_performance_model'
TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
PKG_PATH = os.path.abspath(os.path.join(
    TESTS_DIR, '..', '..', 'examples', PROJECT
))
PROJ_PATH = os.path.join(PKG_PATH, PROJECT.lower())

sys.path.append(PKG_PATH)
sandia_performance_model = importlib.import_module(
    '.%s' % MODEL, PROJECT.lower()
)
