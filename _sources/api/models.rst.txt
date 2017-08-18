.. _models:

Models
======
.. automodule:: carousel.core.models

Model Parameter
---------------
.. autoclass:: ModelParameter

   :param str layer: name of the layer class of these parameters, optional
   :param str module: module that the sources are defined in, optional
   :param str package: package that the source module is contained in, optional
   :param str path: path to source package if not on ``PYTHONPATH``, optional
   :param list sources: name of classes with each layers parameters

Model Base
----------
.. autoclass:: ModelBase
   :members:

Model
-----
.. autoclass:: Model
   :members:
