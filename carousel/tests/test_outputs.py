"""
test outputs
"""

from nose.tools import ok_, eq_
from carousel.core.outputs import Output
from carousel.tests import PROJ_PATH
import os


def test_outputs_metaclass():
    """
    Test Output Sources
    """

    class OutputTest1(Output):
        class Meta:
            outputs_file = 'pvpower.json'
            outputs_path = os.path.join(PROJ_PATH, 'outputs')

    out_src_test1 = OutputTest1()
    ok_(isinstance(out_src_test1, Output))
    eq_(out_src_test1.param_file,
        os.path.join(PROJ_PATH, 'outputs', 'pvpower.json'))

    class OutputTest2(Output):
        timestamps = {"isconstant": True, "size": 8761}
        hourly_energy = {
                             "isconstant": True,
                             "timeseries": "hourly_timeseries", "units": "W*h",
                             "size": 8760
                         }
        hourly_timeseries = {"isconstant": True, "units": "W*h", "size": 8760}
        monthly_energy = {"isconstant": True, "units": "W*h", "size": 12}
        annual_energy = {"isconstant": True, "units": "W*h"}

    out_src_test2 = OutputTest2()
    ok_(isinstance(out_src_test2, Output))
    for k, v in out_src_test2.parameters.iteritems():
        eq_(out_src_test1.parameters[k], v)
