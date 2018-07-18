.. _tutorial-3:

Tutorial 3: Formulas
====================
In the :ref:`last tutorial <tutorial-2>` we created a calculation that used data
and outputs as arguments in formulas that resulted in new output values. In this
tutorial we'll create the formulas that are used in calculations.

Formulas
--------
Formulas are functions or equations that take input arguments and return values.
SimKit currently supports formulas that are written in Python as function
definitions or strings that can be evaluated by the Python
`numexpr <https://pypi.python.org/pypi/numexpr>`_ package. For the PV system
power example, we will use formulas written as Python functions. To add the
formulas we need for this example create a Python package in our project package
called ``formulas``, don't forget to add ``__init__.py`` to make it a package,
and copy the following code into a Python module called ``utils.py`` inside the
formulas folder, *i.e.*: ``PVPower/pvpower/formulas/utils.py``. ::

    # -*- coding: utf-8 -*-

    """
    This module contains formulas for calculating PV power.
    """

    import numpy as np
    from scipy import constants as sc_const
    import itertools
    from dateutil import rrule


    def f_energy(ac_power, times):
        """
        Calculate the total energy accumulated from AC power at the end of each
        timestep between the given times.

        :param ac_power: AC Power [W]
        :param times: times
        :type times: np.datetime64[s]
        :return: energy [W*h] and energy times
        """
        dt = np.diff(times)  # calculate timesteps
        # convert timedeltas to quantities
        dt = dt.astype('timedelta64[s]').astype('float') / sc_const.hour
        # energy accumulate during timestep
        energy = dt * (ac_power[:-1] + ac_power[1:]) / 2
        return energy, times[1:]


    def groupby_freq(items, times, freq, wkst='SU'):
        """
        Group timeseries by frequency. The frequency must be a string in the
        following list: YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY or
        SECONDLY. The optional weekstart must be a string in the following list:
        MO, TU, WE, TH, FR, SA and SU.

        :param items: items in timeseries
        :param times: times corresponding to items
        :param freq: One of the ``dateutil.rrule`` frequency constants
        :type freq: str
        :param wkst: One of the ``dateutil.rrule`` weekday constants
        :type wkst: str
        :return: generator
        """
        timeseries = zip(times, items)  # timeseries map of items
        # create a key lambda to group timeseries by
        if freq.upper() == 'DAILY':
            def key(ts_): return ts_[0].day
        elif freq.upper() == 'WEEKLY':
            weekday = getattr(rrule, wkst.upper())  # weekday start
            # generator that searches times for weekday start
            days = (day for day in times if day.weekday() == weekday.weekday)
            day0 = days.next()  # first weekday start of all times

            def key(ts_): return (ts_[0] - day0).days // 7
        else:
            def key(ts_): return getattr(ts_[0], freq.lower()[:-2])
        for k, ts in itertools.groupby(timeseries, key):
            yield k, ts


    def f_rollup(items, times, freq):
        """
        Use :func:`groupby_freq` to rollup items

        :param items: items in timeseries
        :param times: times corresponding to items
        :param freq: One of the ``dateutil.rrule`` frequency constants
        :type freq: str
        """
        rollup = [np.sum(item for __, item in ts)
                  for _, ts in groupby_freq(items, times, freq)]
        return np.array(rollup)

Formulas can use any code or packages necessary. However here are a couple of
conventions that may be helpful.

* keep formulas short
* name formulas after the main output preceeded by ``f_`` - SimKit can be
  configured to search for functions with this prefix
* use NumPy arrays for arguments so uncertainty and units are propagated
* document functions verbosely
* group related formulas together in the same module or file

Formula Class
-------------
We'll use the same ``performance.py`` module again that we used in the previous
tutorials to add these formulas to our model. We'll need to import
:class:`~simkit.core.formulas.Formula` and
:class:`~simkit.core.formulas.FormulaParameter`. Then we'll list the formulas
as class attributes and their attributes, like ``args`` and ``units``, as
formula parameter arguments. Finally we put the module and package where we
import the corresponding Python functions from in a nested ``Meta`` class. Note
that the formulas have the same names as the Python functions. ::

    from simkit.core.formulas import Formula, FormulaParameter


    class UtilityFormulas(Formula):
        """
        Formulas for PV Power demo
        """
        f_daterange = FormulaParameter()
        f_energy = FormulaParameter(
            args=["ac_power", "times"],
            units=[["watt_hour", None], ["W", None]]
        )
        f_rollup = FormulaParameter(
            args=["items", "times", "freq"],
            units=["=A", ["=A", None, None]]
        )

        class Meta:
            module = ".utils"
            package = "pvpower.formulas"


Formula Attributes
------------------
All of the formulas and formula attributes are defined as class attributes using
formula parameters. If formula attributes are provided as positional arguments,
the order is given in the table below, but keyword arguments can be passed to
:class:`~simkit.core.formulas.FormulaParameter` in any order.

+------------+----------------------------------------------------------------+
| Attribute  | Description                                                    |
+============+================================================================+
| islinear   | flag to indicate linear vs nonlinear formulas [not used]       |
+------------+----------------------------------------------------------------+
| args       | list of names of input arguments                               |
+------------+----------------------------------------------------------------+
| units      | list of return value and input argument units for the Pint     |
|            | method                                                         |
|            | `wraps <http://pint.readthedocs.io/en/latest/wrapping.html>`_  |
+------------+----------------------------------------------------------------+
| isconstant | list of arguments that don't have any covariance               |
+------------+----------------------------------------------------------------+

Formula Importers
-----------------
Formulas can be written as Python functions or as strings that are evaluated
using the Python `numexpr <https://pypi.python.org/pypi/numexpr>`_ package.
SimKit uses :class:`~simkit.core.formulas.FormulaImporter` to create
callable objects from the formulas specified by the formula class. The formula
importer can be specified as a ``Meta`` class option in the formula class using
``formula_importer``, otherwise the default is
:class:`~simkit.core.formulas.PyModuleImporter`.

Python Module Importer
~~~~~~~~~~~~~~~~~~~~~~
If formulas are written in Python and use the default ``FormulaImporter`` for
Python modules, :class:`~simkit.core.formulas.PyModuleImporter`, then we need
to specify the path, package, and module that contains the function definitions.
This information is specified for the entire formula class in it's ``Meta``
class options. If the module is in a package, then the full namespace of the
module can be specified or the relative module name and the package. If the
module or its package are on the Python path, then that's enough to import the
formulas. Otherwise specify the path to the module or package as well. ::

    from simkit.core.formulas import Formula, PyModuleImporter


    class Utils(Formula):
        class Meta:
            formula_importer = PyModuleImporter
            module = '.utils'  # relative module name
            package = 'pvpower.formulas'  # module package
            path = 'examples/PVPower'  # path to package if not on PYTHONPATH


    class Irradiance(Formula):
        class Meta:
            formula_importer = PyModuleImporter
            module = 'irradiance'  # module name
            package = None # no package
            path = 'examples/PVPower/pvpower/formulas'  # path to module


    class Performance(formulas.Formula):
        class Meta:
            formula_importer = PyModuleImporter
            module = 'pvpower.formulas.performance'  # module name with package
            package = None
            path = 'examples/PVPower'  # path to package


=================  ==========================================================
Meta Class Option   Description
=================  ==========================================================
formula_importer   ``FormulaImporter`` subclass that can import functions
module             name of the module containing formulas as Python functions
package            package containing Python functions used as formulas
path               path to folder containing formulas module or package
=================  ==========================================================


The formulas should be given as individual formula parameters. If there are no
formula parameters in the formula class then any function preceded with ``f_``
in the module specified in the ``Meta`` class options will be imported as a
formula, and arguments will be inferred using :func:`inspect.getargspec` but no
units or uncertainty will be propagated, and SimKit will log an
``AttributeError`` as a warning.

Numerical Expressions Importer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Formulas can be written as string expressions that are evaluated using the
Python `numexpr <https://pypi.python.org/pypi/numexpr>`_ package. These formulas
are specified by passing the string as the ``expression`` argument, a list of
the arguments as ``args``, and any other desired formula attributes like
``units`` or ``isconstant`` to :class:`~simkit.core.formulas.FormulaParameter`
and setting the ``formula_importer`` in the ``Meta`` class options to
:class:`~simkit.core.formulas.NumericalExpressionImporter`. For example,
the following formula contains a numerical expression for the Pythagorean
theorem with arguments ``a`` and ``b``, output units that match whatever the
input units are, and propagates uncertainty for all arguments, *ie*: nothing is
constant ::

    class PythagoreanFormula(Formula):
        """
        Formulas to calculate the hypotenuse of a right triangle.
        """
        class Meta:
            formula_importer = NumericalExpressionImporter

        f_hypotenuse = FormulaParameter(
            expression='sqrt(a * a + b * b)',
            args=['a', 'b'],
            units=[('=A', ), ('=A', '=A', None, None)],
            isconstant=[]
        )


Units and Uncertainty
---------------------
SimKit uses `Pint <http://pint.readthedocs.io/>`_, a Python package that
converts and validates units. Pint provides a
`wrapper <http://pint.readthedocs.io/en/latest/wrapping.html>`_ that checks
and converts specified units of function arguments going into a function and
then applies the desired units to the return values. The units are stripped from
the arguments passed to the original function so it doesn't impose any
additional constraints or increase computation time. Specify the arguments for
the Pint wrapper in the units formula attribute. If units attribute is None or
missing, then SimKit does not wrap the formula.

.. warning::
   SimKit is incompatible with Pint-0.8, please downgrade to v0.7.2, see
   :ref:`caramel_corn` for more details.

SimKit uses
`UncertaintyWrapper <http://sunpower.github.io/UncertaintyWrapper/>`_ to
propagate uncertainty across formulas. Uncertainties are specified in the data
which will be discussed in the :ref:`next tutorial <tutorial-4>`. In order to
propagate uncertainty correctly, especially for multiple argument, multiple
return value or vectorized calculations, the return value may need to be
reshaped so that it is a 2-dimensional NumPy array with the number of return
values on the first axis and the number of observations on the second axis.

For more detail about when and how formulas should be adjusted for units and
uncertainty wrappers, take a look at the examples in :ref:`tutorial-3-detail`

Arguments
---------
The ``Formula`` class actually determines the order of positional arguments
using the Python Standard Library :mod:`inspect` module, but you can explicitly
state the arguments by passing the ``args`` attribute to the formula parameter.
This can be useful if the function has ``*args`` or ``**kwargs``, for example if
the function is wrapped and the wrapped function has ``*args`` or ``**kwargs``.
If using the numerical expression importer, then you must provide the positional
arguments in order.

Sensitivity
-----------
The uncertainty wrapper also calculates the sensitivity of each function to its
inputs. Set the ``isconstant`` attribute to a list of the terms to *exclude*
from the Jacobian. If ``isconstant`` is missing or ``None`` then the sensitivity
will not be calculated and therefore the uncertainty will not be propagated. To
include all inputs set ``isconstant=[]``.

.. note::
   To include propagate uncertainty for all inputs, set ``isconstant=[]``.
