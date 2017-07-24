.. _tutorial-3:

Tutorial 3: Formulas
====================
In the :ref:`last tutorial <tutorial-2>` we created a calculation that used data
and outputs as arguments in formulas that resulted in new output values. In this
tutorial we'll create the formulas that are used in calculations.

Formulas
--------
Formulas are functions or equations that take input arguments and return values.
Carousel currently supports formulas that are written in Python as function
definitions or strings that can be evaluated by the Python
`numexpr <https://pypi.python.org/pypi/numexpr>`_ package. It's convenient to
group related formulas together in the same module or file. To add the formulas
we need for this example create a Python module in our project formulas folder
called ``utils.py`` and copy the following code. ::

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
* name formulas after the main output preceeded by ``f_`` - Carousel can be
  configured to search for functions with this prefix
* use NumPy arrays for arguments so uncertainty and units are propagated
* document functons verbosely

Formula Class
-------------
We'll use the same ``performance.py`` module again that we used in the previous
tutorials to add these formulas to our model. We'll need to import the
:class:`carousel.core.formulas.Formula` class into our model. Then we'll list
the formulas and attributes that tell Carousel how to use them. ::

    from carousel.core.formulas import Formula


    class UtilityFormulas(Formula):
        """
        Formulas for PV Power demo
        """
        f_daterange = FormulaParameter()
        f_energy = FormulaParameter(
            args = ["ac_power", "times"],
            units = [["watt_hour", None], ["W", None]]
        )
        f_rollup = FormulaParameter(
            args = ["items", "times", "freq"],
            units = ["=A", ["=A", None, None]]
        )

        class Meta:
            module = ".utils"
            package = "formulas"


Formula Attributes
------------------
All of the formulas and formula attributes are defined as class attributes, just
like for outputs and calculations.

+------------+----------------------------------------------------------------+
| Attribute  | Description                                                    |
+============+================================================================+
| args       | list of names of input arguments                               |
+------------+----------------------------------------------------------------+
| units      | list of return value and input argument units for the Pint     |
|            | method                                                         |
|            | `wraps <http://pint.readthedocs.io/en/latest/wrapping.html>`_  |
+------------+----------------------------------------------------------------+
| isconstant | list of arguments that don't have any covariance               |
+------------+----------------------------------------------------------------+
| expression | numerical expression as strings for use with                   |
|            | :class:`~carousel.core.formulas.NumericalExpressionImporter`   |
+------------+----------------------------------------------------------------+
| islinear   | flag to indicate linear vs nonlinear formulas [not used]       |
+------------+----------------------------------------------------------------+

Formula Module or Package
-------------------------
Formulas have some attributes for each formula and some attributes that are
common for all of the formulas defined in the class. For example, if the
formulas are written in Python, we need to specify the module that contains the
function definitions. If the module is in a package, then the full namespace of
the module can be specified or the relative module name and the package. If
the module or its package are on the Python path, then that's enough to import
the formulas. Otherwise specify the path to the module or package as well. ::

    class Utils(Formula):
        module = '.utils'  # relative module name
        package = 'formulas'  # module package
        path = 'examples/PVPower'  # path to package


    class Irradiance(Formula):
        module = 'irradiance'  # module name
        package = None # no package
        path = 'examples/PVPower/formulas'  # path to module


    class Performance(formulas.Formula):
        module = 'formulas.performance'  # full module name including package
        package = None
        path = 'examples/PVPower'  # path to package


==========  ==========================================================
Attribute   Description
==========  ==========================================================
module      name of the module containing formulas as Python functions
package     package containing Python functions used as formulas
path        path to folder containing formulas module or package
==========  ==========================================================

Formula Importers
-----------------
Formulas can be written as Python functions or as strings that are evaluated
using the Python `numexpr <https://pypi.python.org/pypi/numexpr>`_ package.
Carousel uses :class:`carousel.core.formulas.FormulaImporter` to create callable
objects from the formulas specified by the formula class. The formula importer
can be specified as a class attribute in the formula class, otherwise the
default is :class:`~carousel.core.formulas.PyModuleImporter`. For example, the
following formula contains a numerical expression for the Pythagorean theorem
and uses the :class:`~carousel.core.formulas.NumericalExpressionImporter`::

    class PythagoreanFormula(Formula):
        """
        Formulas to calculate the hypotenuse of a right triangle.
        """
        formula_importer = NumericalExpressionImporter
        formulas = {
            'f_hypotenuse': {
                'expression': 'sqrt(a * a + b * b)',
                'args': ['a', 'b'],
                'units': [('=A', ), ('=A', '=A', None, None)],
                'isconstant': []
            }
        }

Formulas written in Python can use the default ``FormulaImporter`` for Python
modules, :class:`~carousel.core.formulas.PyModuleImporter`. The formulas can be
a dictionary, a list or ``None``. If the formulas attribute is missing then any
function preceded with ``f_`` will be imported as a formula. If a list of
formulas is given or if ``formulas`` is missing or ``None``, then arguments will
be inferred using :func:`inspect.getargspec` but no units or uncertainty will be
propagated, and Carousel will log an ``AttributeError`` as a warning.

Units and Uncertainty
---------------------
Carousel uses `Pint <http://pint.readthedocs.io/>`_, a Python package that
converts and validates units. Pint provides a
`wrapper <http://pint.readthedocs.io/en/latest/wrapping.html>`_ that checks
and converts specified units of function arguments going into a function and
then applies the desired units to the return values. The units are stripped from
the arguments passed to the original function so it doesn't impose any
additional constraints or increase computation time. Specify the arguments for
the Pint wrapper in the units formula attribute. If units attribute is None or
missing, then Carousel does not wrap the formula.

Carousel uses
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
Carousel uses :mod:`inspect` to get the order of positional arguments, but you
can specify them explicitly using the ``args`` attribute. If using the numerical
expression importer, then you must provide the positional arguments in order.

Sensitivity
-----------
The uncertainty wrapper also calculates the sensitivity of each function to its
inputs. Set the ``isconstant`` attribute to a list of the terms to include in
the Jacobian. If ``isconstant`` is missing or ``None`` then the sensitivity will
not be calculated and therefore the uncertainty will not be propagated. To
include all inputs set ``isconstant = []``.
