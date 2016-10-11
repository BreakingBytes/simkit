.. _tutorial-4:

Tutorial 4: Data
================
The PV system power demo now has outputs, calculations and formulas defined. To
specify data, subclass :class:`carousel.core.data_sources.DataSource` and
declare each data as a class attribute equal to a dictionary. ::

    from carousel.core.data_sources import DataSource
    from carousel.core import UREG
    from datetime import datetime
    import pvlib


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
Data have attributes for each data like units and uncertainty as well as for the
entire class like the data reader or enabling caching. Some data attributes like
variance are calculated when the data is instantiated. And some attributes are
used by the data reader.

==================  =======================================================
Attribute           Description
==================  =======================================================
units               units from `Pint <http://pint.readthedocs.io/>`_
uncertainty         measure of uncertainty, typically 2-sigma
variance            square of uncertainty
isconstant          doesn't vary in dynamic simulations
timeseries          index of dynamic simulation inputs
data_source         name of the class data definded
data_reader         name of :class:`~carousel.core.data_readers.DataReader`
data_cache_enabled  toggle caching of data from file readers as JSON
==================  =======================================================

Preparing Data
--------------
The data superclass doesn't automatically apply some of the attributes, such as
isconstant and uncertainty; these attributes must be applied in the class in the
``__prepare_data__`` method. This is an abstract method that must be called by
every data source. If there is nothing to prepare, then use ``pass``.

The prepare data method is good place to handle several tasks.
* pop values from one data source to another
* popping uncertainty from one data field and applying it to another
* non-dimensionalize parameters
* set constants

Data Readers
------------
Every data source has one of the :class:`~carousel.core.data_readers.DataReader`
classes. The default is the :class:`~carousel.core.data_reader.JSONReader`. The
data readers collect data depending on the attributes of the parameters
specified in the data source. There are also some newer readers in the
contributions folder, such as :class:`carousel.contrib.readers.ArgumentReader`
and :class:`carousel.contrib.readers.DjangoModelReader`.
