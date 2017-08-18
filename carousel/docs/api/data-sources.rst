.. _data-sources:

Data Sources
============
.. automodule:: carousel.core.data_sources

Data Parameter
--------------
.. autoclass:: DataParameter

   :param units: units of this data parameter
   :param uncertainty: uncertainty
   :param bool isconstant: true if doesn't vary in dynamic simulations
   :param timeseries: index of dynamic simulation inputs

Data Regsitry
-------------
.. autoclass:: DataRegistry
   :members:

Data Source Base
----------------
.. autoclass:: DataSourceBase
   :members:

Data Source
-----------
.. autoclass:: DataSource
   :members:

.. _data-readers:

Data Readers
============
.. automodule:: carousel.core.data_readers

DataReader
----------
.. autoclass:: DataReader
   :members:

JSONReader
----------
.. autoclass:: JSONReader
   :members:
