"""
Carousel Python Model Simulation Framework

Mark Mikofski (c) 2015
"""

import os
import importlib

# try to import Dulwich or create dummies
try:
    from dulwich.contrib.release_robot import get_current_version
    from dulwich.repo import NotGitRepository
except ImportError:
    NotGitRepository = NotImplementedError

    def get_current_version(*args, **kwargs):
        raise NotGitRepository

# Dulwich Release Robot
BASEDIR = os.path.dirname(__file__)  # this directory
PROJDIR = os.path.dirname(BASEDIR)
VER_FILE = 'version'  # name of file to store version
# use release robot to try to get current Git tag
try:
    GIT_TAG = get_current_version(PROJDIR)
except NotGitRepository:
    GIT_TAG = None
# check version file
try:
    version = importlib.import_module('%s.%s' % (__name__, VER_FILE))
except ImportError:
    VERSION = None
else:
    VERSION = version.VERSION
# update version file if it differs from Git tag
if GIT_TAG is not None and VERSION != GIT_TAG:
    with open(os.path.join(BASEDIR, VER_FILE + '.py'), 'w') as vf:
        vf.write('VERSION = "%s"\n' % GIT_TAG)
else:
    GIT_TAG = VERSION  # if Git tag is none use version file
VERSION = GIT_TAG  # version

__author__ = u'Mark Mikofski'
__email__ = u'mark.mikofski@sunpowercorp.com'
__url__ = u'https://github.com/SunPower/Carousel'
__version__ = VERSION
__release__ = u'Carousel'
