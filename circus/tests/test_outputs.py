"""
test outputs
"""

from nose.tools import ok_, eq_
from circus.core.outputs import OutputSources
from circus.tests import PROJ_PATH
import os


def test_outputs_metaclass():

    class OutputsSourceTest1(OutputSources):
        outputs_file = 'pvpower.json'
        outputs_path = os.path.join(PROJ_PATH, 'outputs')

    out_src_test1 = OutputsSourceTest1()
    ok_(isinstance(out_src_test1, OutputSources))
    eq_(out_src_test1.param_file,
        os.path.join(PROJ_PATH, 'outputs', 'pvpower.json'))

    class OutputsSourceTest2(OutputSources):
        HourlyEnergy = {"units": "W*h", "init": 0, "size": 8760}
        MonthlyEnergy = {"units": "W*h", "init": 0, "size": 12}
        AnnualEnergy = {"units": "W*h", "init": 0}
        Pac = {"units": "W", "init": 0, "size": 8760}
        Isc = {"units": "A", "size": 8760}
        Imp = {"units": "A", "size": 8760}
        Voc = {"units": "V", "size": 8760}
        Vmp = {"units": "V", "size": 8760}
        Pmp = {"units": "W", "size": 8760}
        Ee = {"units": "dimensionless", "size": 8760}
        Tcell = {"units": "degC", "size": 8760}
        poa_global = {"units": "W/m**2", "size": 8760}
        poa_direct = {"units": "W/m**2", "size": 8760}
        poa_diffuse = {"units": "W/m**2", "size": 8760}
        aoi = {"units": "deg", "size": 8760}
        solar_zenith = {"units": "deg", "size": 8760}
        solar_azimuth = {"units": "deg", "size": 8760}

    out_src_test2 = OutputsSourceTest2()
    ok_(isinstance(out_src_test2, OutputSources))
    for k, v in out_src_test2.parameters.iteritems():
        eq_(out_src_test1.parameters[k], v)
