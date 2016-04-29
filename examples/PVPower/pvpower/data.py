"""
Data sources for PV Power demo.
"""

from circus.core.data_sources import DataSource
import os
from pvpower import PROJ_PATH
from datetime import datetime
import pvlib

DATA_PATH = os.path.join(PROJ_PATH, 'data')


class PVPowerData(DataSource):
    data_file = 'pvpower.json'
    data_path = DATA_PATH

    def __prepare_data__(self):
        # set frequencies
        for k in ('HOURLY', 'MONTHLY', 'YEARLY'):
            self.data[k] = k
            self.isconstant[k] = True
        # apply metadata
        for k, v in self.parameters.iteritems():
            # TODO: this should be applied in data reader using _meta_names from
            # data registry which should use a meta class and all parameter
            # files should have same layout even xlrd and numpy readers, etc.
            if 'isconstant' in v:
                self.isconstant[k] = v['isconstant']
        # convert initial timestamp to datetime
        self.data['timestamp_start'] = datetime(*self.data['timestamp_start'])
        # get module and inverter databases
        self.data['module_database'] = pvlib.pvsystem.retrieve_sam(
            self.data['module_database']
        )
        self.data['inverter_database'] = pvlib.pvsystem.retrieve_sam(
            self.data['inverter_database']
        )
        # get module and inverter
        self.data['module'] = self.data['module_database'][self.data['module']]
        self.data['inverter'] = (
            self.data['inverter_database'][self.data['inverter']]
        )

