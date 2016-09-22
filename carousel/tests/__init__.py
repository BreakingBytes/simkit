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

# using imp interferes with pvpower tests so comment out

# import imp
# PVPOWER_PKG = PROJECT.lower()
#
# # pvpower package
# fid, fn, info = imp.find_module(PVPOWER_PKG, [PROJ_PATH])
# LOGGER.debug('filename: %s', fn)
# try:
#     PVPOWER_PKG = imp.load_module(PVPOWER_PKG, fid, fn, info)
# finally:
#     if fid:
#         fid.close()
# LOGGER.debug('package: %r', PVPOWER_PKG)
# PVPOWER_MOD = '%s.%s' % (PVPOWER_PKG.__name__, MODEL)
# # pvpower model
# fid, fn, info = imp.find_module(MODEL, PVPOWER_PKG.__path__)
# try:
#     sandia_performance_model = imp.load_module(PVPOWER_MOD, fid, fn, info)
# finally:
#     if fid:
#         fid.close()
