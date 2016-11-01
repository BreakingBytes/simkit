"""
Carousel Python Model Simulation Framework

Mark Mikofski (c) 2015
"""

from dulwich.repo import Repo
from dulwich.objects import Tag
import time
import datetime
import logging
import os

DIRNAME = os.path.abspath(os.path.dirname(__file__))
PROJDIR = os.path.dirname(DIRNAME)
logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

def get_recent_tags(projdir=PROJDIR):
    project = Repo(projdir)
    refs = project.get_refs()
    tags = {}
    for key, value in refs.iteritems():
        obj = project.get_object(value)
        if isinstance(obj, Tag):
            _, tag = key.rsplit('/', 1)
            tagtime = time.gmtime(obj.tag_time)
            tags[tag] = datetime.datetime(*tagtime[:6])
            LOGGER.debug('%s: %s', tag, tags[tag].isoformat())
    return sorted(tags.iteritems(), key=lambda tag: tag[1], reverse=True)


__author__ = u'Mark Mikofski'
__email__ = u'mark.mikofski@sunpowercorp.com'
__url__ = u'https://github.com/SunPower/Carousel'
__version__ = get_recent_tags()[0][0][1:]
__release__ = u'Cotton Candy'