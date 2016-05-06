#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Creates a basic file structure to start a Carousel project.

    Project
    |
    +-+- project
    | |
    | +- __init__.py
    |
    +- models
    | |
    | +- default.json
    |
    +- simulation
    |
    +- outputs
    |
    +- calculations
    |
    +- formulas
    |
    +- data
"""

# import argparse
import json
import logging
import os
import re
# import shutil
import sys

# set up logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# constants
CWD = os.getcwd()
OKAY = r'[\w\d]'
LAYERS = ['simulations', 'outputs', 'calculations', 'formulas', 'data']
DFLT_MODEL = dict.fromkeys(LAYERS)
DFLT = 'my_model.json'
MODELS = 'models'
PATHS = [MODELS] + LAYERS

# run from command line
if __name__ == '__main__':
    # exit with error if no project name specified
    if len(sys.argv) < 2:
        sys.exit('No project directory was specified.')
    project_name = sys.argv[1]  # get project name
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
    # make project file structure
    for p in PATHS + [project_pkg]:
        os.mkdir(os.path.join(project_name, p))
        LOGGER.debug('created folder: %s', p)
    # make project package
    pkg_init = os.path.join(project_name, project_pkg, '__init__.py')
    with open(pkg_init, 'w') as init:
        init.write('"""\nThis is the %s package.\n"""\n' % project_pkg)
    # make default model
    with open(os.path.join(project_name, MODELS, DFLT), 'w') as dflt:
        json.dump(DFLT_MODEL, dflt, indent=2)
        LOGGER.debug('created %s in %s/%s', DFLT, project_name, MODELS)
