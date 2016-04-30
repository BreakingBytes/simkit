"""
test outputs
"""

from nose.tools import ok_, eq_
from flying_circus.core.outputs import Output
from flying_circus.tests import PROJ_PATH
import os


def test_outputs_metaclass():
    """
    Test Output Sources
    """

    class OutputTest1(Output):
        outputs_file = 'pvpower.json'
        outputs_path = os.path.join(PROJ_PATH, 'outputs')

    out_src_test1 = OutputTest1()
    ok_(isinstance(out_src_test1, Output))
    eq_(out_src_test1.param_file,
        os.path.join(PROJ_PATH, 'outputs', 'pvpower.json'))

    class OutputTest2(Output):
        timeseries = {"isconstant": True, "size": 8761}
        hourly_energy = {"units": "W*h", "init": 0, "size": 8760}
        hourly_timeseries = {"units": "W*h", "init": 0, "size": 8760}
        monthly_energy = {"units": "W*h", "init": 0, "size": 12}
        annual_energy = {"units": "W*h", "init": 0}
        Pac = {"units": "W", "init": 0, "size": 8761}
        Isc = {"units": "A", "size": 8761}
        Imp = {"units": "A", "size": 8761}
        Voc = {"units": "V", "size": 8761}
        Vmp = {"units": "V", "size": 8761}
        Pmp = {"units": "W", "size": 8761}
        Ee = {"units": "dimensionless", "size": 8761}
        Tcell = {"units": "degC", "size": 8761}
        poa_global = {"units": "W/m**2", "size": 8761}
        poa_direct = {"units": "W/m**2", "size": 8761}
        poa_diffuse = {"units": "W/m**2", "size": 8761}
        aoi = {"units": "deg", "size": 8761}
        solar_zenith = {"units": "deg", "size": 8761}
        solar_azimuth = {"units": "deg", "size": 8761}

    out_src_test2 = OutputTest2()
    ok_(isinstance(out_src_test2, Output))
    for k, v in out_src_test2.parameters.iteritems():
        eq_(out_src_test1.parameters[k], v)
