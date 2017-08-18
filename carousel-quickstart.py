#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
carousel-quickstart.py command-line script - more info in docs/api/scripts
"""

import argparse
import logging
import os
import re
from carousel import __version__
import sys
from dulwich import porcelain, config as gitconfig

# set up logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# constants
CWD = os.getcwd()
OKAY = r'[\w\d]'
INIT_CONTENT = """
import os

__version__ = '0.1'
__author__ = '%s'
__email__ = '%s'

PROJ_PATH = os.path.abspath(os.path.dirname(__file__))
# TODO: change PROJ_PATH to MODELPATH everywhere
"""
DESCRIPTION = """
Create a Carousel project file structure. See documentation for more detail.
"""
GIT_GLOBAL = os.path.expanduser(os.path.join('~', '.gitconfig'))
UNKNOWN = 'unknown'
USERNAME = (os.environ.get('USERNAME', UNKNOWN) if sys.platform == 'win32'
            else os.environ.get('USER', UNKNOWN))  # default username
HOSTNAME = os.uname()[1]
USEREMAIL = '%s@%s' % (USERNAME, HOSTNAME)


def get_gitconfig(git_path, section, name):
    try:
        return gitconfig.ConfigFile.from_path(git_path).get(section, name)
    except (IOError, KeyError):
        return None


# run from command line
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('project', help='name of Carousel project to create')
    parser.add_argument('--version', action='version',
                        version=('%(prog)s' + ' %s' % __version__))
    parser.add_argument('-g', '--git', action='store_true',
                        help='initialize Git repository for project')
    parser.add_argument(
        '-f', '--folders', action='append', default=['data'],
        help=('create layer folders in project package, list each folder'
              ' separately, can be used more than once, default is "data"'))
    parser.add_argument('--author', help="Project author's full name",
                        default=USERNAME)
    parser.add_argument('--email', help="Project author's email",
                        default=USEREMAIL)
    args = parser.parse_args()
    # exit with error if no project name specified
    if len(sys.argv) < 2:
        sys.exit('No project directory was specified.')
    project_name = args.project  # get project name
    # check if name is alpha-numeric, underscore okay
    match = re.findall(OKAY, project_name)  # find all alpha-numeric matches
    clean = ''.join(match)  # clean alpha-numeric project name
    if not match or clean != project_name:
        sys.exit('The specified project, %s, ' % project_name +
                 'is not alpha-numeric. Try "%s" instead.' % clean)
    project_pkg = project_name.lower()
    project_name = os.path.join(CWD, project_name)  # full path to project
    # check if path already exists
    if os.path.exists(project_name):
        sys.exit('The path, %s, already exists.' % project_name)
    os.mkdir(project_name)  # make project folder
    LOGGER.info('Project created at path, %s.', project_name)
    # make project package
    os.mkdir(os.path.join(project_name, project_pkg))  # make project package
    LOGGER.info('Project package, %s, created.', project_pkg)
    pkg_init = os.path.join(project_name, project_pkg, '__init__.py')
    # try to get user info from git config
    username = useremail = None
    if args.author == USERNAME:
        username = get_gitconfig(GIT_GLOBAL, 'user', 'name')
        if username:
            args.author = username
    if args.email == USEREMAIL:
        useremail = get_gitconfig(GIT_GLOBAL, 'user', 'email')
        if useremail:
            args.email = useremail
    with open(pkg_init, 'w') as init:
        init.write('"""\nThis is the %s package.\n"""\n' % project_pkg)
        init.write(INIT_CONTENT % (args.author, args.email))
    LOGGER.info('Package file created: %s.', pkg_init)
    if args.git:
        repo = porcelain.init(project_name)
        LOGGER.info('Project Git repository initialized: %s.', repo)
        porcelain.add(repo, os.path.relpath(pkg_init, project_name))
        LOGGER.info('Project package added to index')
        # if global git config username and email not set, use args if specified
        kwargs = {}
        if not username:
            username = args.author
        if not useremail:
            useremail = args.email
        if not os.path.exists(GIT_GLOBAL):
            conf = repo.get_config()
            conf.set('user', 'name', username)
            conf.set('user', 'email', useremail)
            conf.write_to_path()
        else:
            kwargs['author'] = '%s <%s>' % (username, useremail)
        sha1 = porcelain.commit(repo, message='initial dump', **kwargs)
        LOGGER.info('Project initial commit: %s.', sha1)
        porcelain.log(repo, outstream=logging.root.handlers[0].stream)
    # make project layer folders
    for fp in args.folders:
        os.mkdir(os.path.join(project_name, project_pkg, fp))
        LOGGER.info('created folder: %s', fp)
    LOGGER.info('Carousel quickstart completed.')
