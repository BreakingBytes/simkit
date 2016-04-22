"""
Outputs for PV Power demo
"""

from circus.core.outputs import OutputSources
import os
from pvpower import PROJ_PATH


class PVPowerOutputs(OutputSources):
    outputs_file = 'pvpower.json'
    outputs_path = os.path.join(PROJ_PATH, 'outputs')
