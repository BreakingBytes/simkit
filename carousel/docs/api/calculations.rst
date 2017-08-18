.. _calculations:

Calculations
============
.. automodule:: carousel.core.calculations

Calculation Parameter
---------------------
.. autoclass:: CalcParameter

   :param list dependencies: required calculations
   :param bool always_calc: calculations ignore simulation thresholds
   :param frequency: dynamic calculations different from timestep
   :param str formula: name of a function
   :param dict args: dictionary of data and outputs
   :param list returns: name(s) of outputs
   :param calculator: calculator class used to calculate this
   :type calculator: :class:`~carousel.core.calculators.Calculator`
   :param bool is_dynamic: true if this is a periodic calculation [``False``]

Calculation Registry
--------------------
.. autoclass:: CalcRegistry

Calculation Base
----------------
.. autoclass:: CalcBase

Calculation
-----------
.. autoclass:: Calc

Calculators
===========
.. automodule:: carousel.core.calculators

Calculator
----------
.. autoclass:: Calculator
   :members:
