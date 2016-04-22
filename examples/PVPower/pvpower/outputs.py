"""
Outputs for PV Power demo
"""

from circus.core.outputs import Output
import os
from pvpower import PROJ_PATH


class PVPowerOutputs(Output):
    outputs_file = 'pvpower.json'
    outputs_path = os.path.join(PROJ_PATH, 'outputs')
