.. _formulas:

Formulas
========
.. automodule:: carousel.core.formulas

Formula Parameter
-----------------
.. autoclass:: FormulaParameter

   :param bool islinear: flag to indicate nonlinear formulas [not used]
   :param list args: list of names of input arguments
   :param list units: list of return value and input argument units for Pint
      `wrapping <http://pint.readthedocs.io/en/latest/wrapping.html>`_
   :param list isconstant: list of arguments that don’t have any covariance


Formula Registry
----------------
.. autoclass:: FormulaRegistry
   :members:

Formula Importers
-----------------
.. autoclass:: FormulaImporter
   :members:

Python Module Importer
~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: PyModuleImporter
   :members:

Numerical Expression Importer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: NumericalExpressionImporter
   :members:

Formula Base
------------
.. autoclass:: FormulaBase
   :members:

Formula
-------
.. autoclass:: Formula
   :members:
