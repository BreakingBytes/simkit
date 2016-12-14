"""
Carousel Python Model Simulation Framework

Mark Mikofski (c) 2015
"""

from carousel.release_robot import get_current_version
from dulwich.repo import NotGitRepository
import os

BASEDIR = os.path.dirname(__file__)


def get_or_create_version(verfile='version.py'):
    try:
        git_version = get_current_version()
    except (ImportError, NotGitRepository):
        git_version = None
    try:
        from carousel.version import VERSION
    except ImportError:
        VERSION = None
    if git_version is not None and VERSION != git_version:
        with open(os.path.join(BASEDIR, verfile), 'w') as vf:
            vf.write('VERSION = "%s"\n' % git_version)
    else:
        git_version = VERSION
    return git_version


__author__ = u'Mark Mikofski'
__email__ = u'mark.mikofski@sunpowercorp.com'
__url__ = u'https://github.com/SunPower/Carousel'
__version__ = get_or_create_version()
__release__ = u'Caramel Corn'
