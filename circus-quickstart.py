"""
Creates a basic file structure to start a Circus project.

    Project
    |
    +- models
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

import os
import shutil
import sys

DIRNAME = os.path.dirname(__file__)
BAD = '<>:"/\|?*'
PATHS = ['models', 'simulations', 'outputs', 'calculations', 'formulas', 'data']

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(-1)
    project_name = sys.argv[1]
    if any(c in BAD for c in project_name):
        sys.exit(-2)
    project_name = os.path.join(DIRNAME, project_name)
    os.mkdir(project_name)
    for p in PATHS:
        os.mkdir(os.path.join(project_name, p))
