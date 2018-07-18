.. _tutorial-4:

Tutorial 4: Data
================
The PV system power demo now has outputs, calculations and formulas defined. Now
it just needs some data. Data are values that are read from sources such as an
Excel workbook or a CSV file. Data are different from outputs because data are
known before a simulation, whereas outputs are calculated during the simulation.
To specify data, subclass :class:`~simkit.core.data_sources.DataSource` and
declare each data by name as class attributes equal to an instance of
:class:`~simkit.core.data_sources.DataParameter` containing the
:ref:`data-attrs` as arguments. Here's an example for our PV system power
model::

    from simkit.core.data_sources import DataSource, DataParameter
    from simkit.core import UREG
    from datetime import datetime
    import pvlib


    class PVPowerData(DataSource):
        """
        Data sources for PV Power demo.
        """
        latitude = DataParameter(units="degrees", uncertainty=1.0)
        longitude = DataParameter(units="degrees", uncertainty=1.0)
        elevation = DataParameter(units="meters", uncertainty=1.0)
        timestamp_start = DataParameter()
        timestamp_count = DataParameter()
        module = DataParameter()  # a dictionary
        inverter = DataParameter()  # a dictionary
        module_database = DataParameter()  # a list
        inverter_database = DataParameter()  # a list
        Tamb = DataParameter(units="degC", uncertainty=1.0)
        Uwind = DataParameter(units="m/s", uncertainty=1.0)
        surface_azimuth = DataParameter(units="degrees", uncertainty=1.0)
        timezone = DataParameter()

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

.. _data-attrs:

Data Attributes
---------------
The following data attributes can be passed as arguments to each data parameter.
If using positional arguments, then their order is given in the table below, but
keyword arguments can be passed to ``DataParameter`` in any order.

==================  =======================================================
Attribute           Description
==================  =======================================================
units               units from `Pint <http://pint.readthedocs.io/>`_
uncertainty         measure of uncertainty, typically 2-sigma
isconstant          doesn't vary in dynamic simulations
timeseries          index of dynamic simulation inputs
==================  =======================================================

Meta Class Options
------------------
Options that apply to the entire data class like the data reader or enabling
data caching are specified in a nested ``Meta`` class.

==================  =======================================================
Meta Class Option   Description
==================  =======================================================
data_reader         name of :class:`~simkit.core.data_readers.DataReader`
data_cache_enabled  toggle caching of data from file readers as JSON
==================  =======================================================

Uncertainty and Variance
------------------------
Uncertainty should be given in units of percent from :data:`~simkit.core.UREG`
or it will raise :exc:`~simkit.core.exceptions.UncertaintyPercentUnitsError`
when registered in the data registry. Variance is calculated from the square of
the uncertainty when the data is instantiated. The data registry also checks
when it registers new data that variance is the square of the uncertainty or it
raises :exc:`~simkit.core.exceptions.UncertaintyVarianceError`.

Preparing Data
--------------
The data superclass doesn't automatically apply some of the attributes, such as
``isconstant`` and ``uncertainty``; these attributes must be applied in the
data source class ``__prepare_data__`` method, an abstract method that *must* be
concrete in the subclass or it will raise :exc:`exceptions.NotImplementedError`.
If there is nothing to prepare, then use ``pass``.

The prepare data method is good place to handle several tasks.

* pop values from one data source to another
* apply uncertainty
* non-dimensionalize parameters
* set constants
* convert types such as string to datetime

Data Readers
------------
Every data source has one of the :class:`~simkit.core.data_readers.DataReader`
classes. The default is the :class:`~simkit.core.data_readers.JSONReader`. The
data readers collect data depending on the attributes of the parameters
specified in the data source. There are also some newer readers in the
contributions folder, such as :class:`~simkit.contrib.readers.ArgumentReader`
and :class:`~simkit.contrib.readers.DjangoModelReader`.
