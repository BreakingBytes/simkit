"""
FlyingCircus tests
"""

from flying_circus.core import logging
import imp
import os
import sys

LOGGER = logging.getLogger(__name__)
PROJECT = 'PVPower'
MODEL = 'sandia_performance_model'
TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
PROJ_PATH = os.path.abspath(os.path.join(
    TESTS_DIR, '..', '..', 'examples', PROJECT
))
sys.path.append(PROJ_PATH)

fid, fn, info = imp.find_module(MODEL,
                                [os.path.join(PROJ_PATH, PROJECT.lower())])
pvpower_models = imp.load_module(MODEL, fid, fn, info)
fid.close()
