.. _tutorial-4:

Tutorial 4: Data
================
The PV system power demo now has outputs, calculations and formulas defined. To
specify data, subclass :class:`carousel.core.data_sources.DataSource` and
declare each data as a class attribute equal to a dictionary. ::

    class PVPowerData(DataSource):
        """
        Data sources for PV Power demo.
        """
        latitude = {"units": "degrees", "uncertainty": 1.0}
        longitude = {"units": "degrees", "uncertainty": 1.0}
        elevation = {"units": "meters", "uncertainty": 1.0}
        timestamp_start = {}
        timestamp_count = {}
        module = {}
        inverter = {}
        module_database = {}
        inverter_database = {}
        Tamb = {"units": "degC", "uncertainty": 1.0}
        Uwind = {"units": "m/s", "uncertainty": 1.0}
        surface_azimuth = {"units": "degrees", "uncertainty": 1.0}
        timezone = {}

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
                self.isconstant[k] = True  # set all data "isconstant" True
                # uncertainty is dictionary
                if 'uncertainty' in v:
                    self.uncertainty[k] = {k: v['uncertainty'] * UREG.percent}
            # convert initial timestamp to datetime
            self.data['timestamp_start'] = datetime(*self.data['timestamp_start'])
            # get module and inverter databases
            self.data['module_database'] = pvlib.pvsystem.retrieve_sam(
                self.data['module_database'], path=SANDIA_MODULES
            )
            self.data['inverter_database'] = pvlib.pvsystem.retrieve_sam(
                self.data['inverter_database'], path=CEC_INVERTERS
            )
            # get module and inverter
            self.data['module'] = self.data['module_database'][self.data['module']]
            self.data['inverter'] = (
                self.data['inverter_database'][self.data['inverter']]
            )

Data Attributes
---------------
Data have attributes for each data as well as for the entire class.

=============  ================================================
Attribute      Description
=============  ================================================
units          units from `Pint <http://pint.readthedocs.io/>`_
uncertainty    measure of uncertainty, typically 2-sigma
variance       square of uncertainty
isconstant     doesn't vary in dynamic simulations
timeseries     index of dynamic simulation inputs
data_source    name of the class data definded
=============  ================================================
