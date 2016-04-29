"""
PV Power Demo model
"""

from circus.core.models import Circus


class PVPower(Circus):
    def __init__(self, modelfile):
        super(PVPower, self).__init__(modelfile)
        # TODO: pass SAPM as argument or set as class attribute, not hard-coded
        # here. Ditto for name of dt
        dt = self.simulations.simulation['SAPM'].interval  # time-step [time]
        self.data.data.register(newdata={'dt': dt}, uncertainty=None,
                                isconstant={'dt': True}, timeseries=None,
                                data_source=None)
