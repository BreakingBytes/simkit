"""
circus tests
"""

import os
import imp

MODEL = 'PVPower'
TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
PROJ_PATH = os.path.abspath(os.path.join(
    TESTS_DIR, '..', '..', 'examples', MODEL
))

fid, fn, info = imp.find_module('models',
                                [os.path.join(PROJ_PATH, MODEL.lower())])
pvpower_models = imp.load_module('models', fid, fn, info)
fid.close()
