.. _tutorial-2:

Tutorial 2: Calculations
========================
In the :ref:`first tutorial <tutorial-1>` we decided what outputs we wanted from
our PV system power model. In the second tutorial we'll create the calculations
that yield those desired outputs. In SimKit, a *calculation* is a combination
of formulas, data, and outputs that calculates outputs from formulas evaluated
using data and outputs as arguments. Each step in the calculation maps formula
input arguments to data and outputs and the return values to outputs. We already
explained in :ref:`tutorial-1` how SimKit defines *outputs*, and next in
:ref:`tutorial-3` and :ref:`tutorial-4` we'll define what the terms *data* and
*formulas* mean.

Calculation Class
-----------------
Let's keep using the ``performance.py`` module we created in :ref:`tutorial-1`.
We'll need to import the :class:`~simkit.core.calculations.Calc` class to
create a new subclass for the calculations in our PV system power example. To
calculate the hourly energy and corresponding timestamps we'll need to integrate
AC power over time and shift the timestamps to the end of each hour. Therefore
in this example, the hourly energy at the given timestamp corresponds to the
energy accumulated over the previous hour instead of the average power at that
timestamp. We can also roll up the hourly energy to output monthly and annual
values. We need to import the :class:`~simkit.core.calculations.CalcParameter`
class to define these calculation steps. Assuming the AC power and corresponding
timestamps are already outputs, and assuming that functions for energy
integration and roll-ups are already formulas we can specify this calculation as
follows::

    from simkit.core.calculations import Calc, CalcParameter, Calculator


    class UtilityCalcs(Calc):
        """
        Calculations for PV Power demo
        """
        energy = CalcParameter(
            is_dynamic=False,
            calculator=Calculator,
            dependencies=["ac_power", "daterange"],
            formula="f_energy",
            args={"outputs": {"ac_power": "Pac", "times": "timestamps"}},
            returns=["hourly_energy", "hourly_timeseries"]
        )
        monthly_rollup = CalcParameter(
            is_dynamic=False,
            calculator=Calculator,
            dependencies=["energy"],
            formula="f_rollup",
            args={
                "data": {"freq": "MONTHLY"},
                "outputs": {"items": "hourly_energy",
                            "times": "hourly_timeseries"}
            },
            returns=["monthly_energy"]
        )
        yearly_rollup = CalcParameter(
            is_dynamic=False,
            calculator=Calculator,
            dependencies=["energy"],
            formula="f_rollup",
            args={"data": {"freq": "YEARLY"},
                  "outputs": {"items": "hourly_energy",
                              "times": "hourly_timeseries"}},
            returns=["annual_energy"]
        )
            
Calculation Attributes
----------------------
In the snippet above, the calculation is called ``UtilityCalcs``, and it defines
three calculation parameters: ``energy``, ``monthly_rollup``, and
``yearly_rollup``. Each calculation parameter has keyword arguments like
`dependencies <http://xkcd.com/754/>`_, ``always_calc``, and ``frequency``,
that describe attributes about the calculation parameter. All calculations
parameters and their attributes are stored in the calculation registry which the
simulation uses to run the model.

Formulas, Arguments, and Returns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Calculations are sets of calculation parameters that describe the steps required
to calculate the desired outputs. Each step is a ``CalcParameter`` that must at
least contain ``formula``, ``args`` and ``returns``. The value of each is a
reference to the value in the corresponding registry. For example, in the
``UtilityCalc`` snippet above, the first calculation parameter, ``energy``, uses
the formula ``f_energy`` which is the key for the corresponding function in the
:class:`~simkit.core.formulas.FormulaRegistry`. The arguments to the formula
are given by ``args`` which is a dictionary that maps the formula inputs with
either ``data`` form the :class:`~simkit.core.data_sources.DataRegistry` or
``outputs`` from the :class:`~simkit.core.outputs.OutputRegistry`. The first
key in ``args`` tells you which registry and the following dictionary maps the
formula inputs to the registry keys. For example, ``f_energy`` takes two inputs:
``ac_power`` and ``times``. To calculate ``energy`` we use the outputs: ``Pac``
and ``timestamps``. Formulas can be used with different arguments to return
different outputs by referring to different values in the data and output
registries respectively. For example, notice how ``f_rollup`` is used twice,
once with the ``freq`` argument set to the value of the data ``MONTHLY`` and
return value set to the output ``monthly_energy`` and then again with data
``YEARLY`` and output ``annual_energy``.

The following table lists the attributes that calculations can have. If given as
positional arguments, then the order is the same as the table below; keyword
arguments can be in any order.

============  ============================================  ==============
Attribute     Description                                   Default
============  ============================================  ==============
dependencies  list of required calculations                 required
always_calc   calculations ignore simulation thresholds     ``False``
frequency     dynamic calculations different from timestep  1-interval
formula       name of a function                            required
args          dictionary of data and outputs                required
returns       name of outputs                               required
calculator    calculator class used to calculate this       ``Calculator``
is_dynamic    true if this is a periodic calculation        ``False``
============  ============================================  ==============

Static and Dynamic Calculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``is_dynamic`` attribute indicates whether the calculation parameter has a
time dependency or whether it is calculated once at the beginning of a
simulation. The simulation first calculates parameters with
``is_dynamic==False`` then loops over calculations with ``is_dynamic==True``
for each timestep. The default value of ``is_dynamic`` is ``False``.

Dynamic Calculations
````````````````````
Dynamic calculations depend on a previous timestep. To refer to arguments from
previous timesteps use an index or to refer to a prior time use a quantity. In
the example below, encapsulant browning depends on the previous timestep and the
temperatures from the previous day. ::

    encapsulant_browning = CalcParameter(
        formula="f_encapsulant_browning",
        args={
            "data": {"encapsulant": "encapsulant"},
            "outputs": {
                "prev_encapsulant_browning": ["encapsulant_browning", -1],
                "prev_day_cell_temp": ["Tcell", -1, "day"]
            }
        },
        returns=["encapsulant_browning"]
    )

Calculators
~~~~~~~~~~~
The ``calculator`` attribute sets the ``Calculator`` class used to evaluate the
calculation. The default is :class:`~simkit.core.calculators.Calculator` but
can be overriden to change how the calculation is performed. A ``Calculator``
should implement a :meth:`~simkit.core.calculators.Calculator.calculate`
method that takes the following arguments:

1. dictionary of parameter ``formula``, ``args`` and ``return`` keys
2. formula registry
3. data registry
4. outputs registry

For dynamic calculations, the ``calculate`` method should take these additional
arguments:

5. timestep, defaults to ``None`` for static calculations
6. index, defaults to ``None`` for static calculations

.. versionadded:: 0.3.1

Meta Class Options
~~~~~~~~~~~~~~~~~~
Calculation attributes can be specified for all parameters in a calculation by
declaring them in a nested ``Meta`` class. If individual parameters also declare
the same attributes, then the parameter value will override the ``Meta`` class
value. For example, in the ``UtilityCalcs`` example, the attributes
``is_dynamic`` and ``calculator`` are declared for all three parameters. Instead
these attributes could just be declared for all parameters in ``UtilityCalcs``
by putting them the ``Meta`` class. ::

    class UtilityCalcs(Calc):
        """
        Calculations for PV Power demo
        """
        # same calculation parameters as above without is_dynamic and calculator

        # default attributes for all parameters
        class Meta:
            is_dynamic = False
            calculator = Calculator

Parameter File
--------------
Calculations can also be specified in a parameter file. For example copy the
following into ``PVPower/calculations/utils.json``::

    {
      "energy": {
        "is_dynamic": false,
        "dependencies": ["ac_power", "daterange"],
        "formula": "f_energy",
        "args": {
          "outputs": {"ac_power": "Pac", "times": "timestamps"}
        },
        "returns": ["hourly_energy", "hourly_timeseries"]
      },
      "monthly_rollup": {
        "is_dynamic": false,
        "dependencies": ["energy"],
        "formula": "f_rollup",
        "args": {
          "data": {"freq": "MONTHLY"},
          "outputs": {"items": "hourly_energy", "times": "hourly_timeseries"}
        },
        "returns": ["monthly_energy"]
      },
      "yearly_rollup": {
        "is_dynamic": false,
        "dependencies": ["energy"],
        "formula": "f_rollup",
        "args": {
          "data": {"freq": "YEARLY"},
          "outputs": {"items": "hourly_energy", "times": "hourly_timeseries"}
        },
        "returns": ["annual_energy"]
      }
    }

Just like the :class:`~simkit.core.outputs.Output` class, we tell SimKit
about our calculations by specifying the parameter file in a
:class:`~simkit.core.calculations.Calc` class. Create a new Python module
in the pvpower package called ``performance.py``, like we did above and add a
:class:`~simkit.core.calculations.Calc` class for each calculation. ::

    from simkit.core.calculations import Calc
    import os
    from pvpower import PROJ_PATH


    class UtilityCalcs(Calc):
        outputs_file = 'utils.json'
        outputs_path = os.path.join(PROJ_PATH, 'calculations')

