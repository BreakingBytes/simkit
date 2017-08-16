.. _tutorial-2:

Tutorial 2: Calculations
========================
In the :ref:`first tutorial <tutorial-1>` we decided what outputs we wanted from
our PV system power model. In the second tutorial we'll create the calculations
that yield those desired outputs. In Carousel, a *calculation* is a combination
of formulas, data, and outputs that calculates outputs from formulas evaluated
using data and outputs as arguments. Each step in the calculation maps formula
input arguments to data and outputs and the return values to outputs. We already
explained in :ref:`tutorial-1` how Carousel defines *outputs*, and next in
:ref:`tutorial-3` and :ref:`tutorial-4` we'll define what the terms *data* and
*formulas* mean.

Calculation Class
-----------------
Let's keep using the ``performance.py`` module we created in :ref:`tutorial-1`.
We'll need to import the :class:`~carousel.core.calculations.Calc` class to
create a new subclass for the calculations in our PV system power example. To
calculate the hourly energy and corresponding timestamps we'll need integrate
AC power over time and shift the timestamps to the end of each hour. Therefore
in this example, the hourly energy at the given timestamp corresponds to the
energy accumulated over the previous hour instead of the average power at that
timestamp. We can also roll up the hourly energy to output monthly and annual
values. We need to import the :class:`~carousel.core.calculations.CalcParameter`
class to define these calculation steps. Assuming the AC power and corresponding
timestamps are already outputs, and assuming that functions for energy
integration and roll-ups are already formulas we can specify this calculation as
follows::

    from carousel.core.calculations import Calc, CalcParameter


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
In the snippet above, the calculation is called ``UtilityCalcs`` and defines a
static calculation as a class attribute. There are other class attributes like
`dependencies <http://xkcd.com/754/>`_ that describe attributes about the
calculation. All calculations and their attributes are stored in the calculation
registry which the simulation uses to run the model. The following table lists
the attributes that calculations can have.

============  ============================================
Attribute     Description
============  ============================================
dependencies  list of required calculations
always_calc   calculations ignore simulation thresholds
frequency     dynamic calculations different from timestep
static        list of one time calculations
dynamic       list of periodic calculations
============  ============================================

Static and Dynamic Calculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The static attribute lists the calculations that are performed once at the
beginning of a simulation and are handled in the simulation by the static
calculator. The dynamic attribute list calculations that have a time dependency.
The simulations loops over dynamic calculations calling the dynamic calculator
at each timestep.

.. versionadded:: 0.3.1

Both static and dynamic calculations are lists that describe the steps required
to calculate the desired outputs. Each step is a dictionary that contains keys
for ``formula``, ``args`` and ``returns``. The value of each key is a reference
to the value in the corresponding registry. Formulas can be used with different
arguments to return different outputs by referring to different values in the
data and output registries respectively. For example, notice how ``f_rollup`` is
used twice, once with the ``freq`` argument set to the value of the data
``MONTHLY`` and return value set to the output ``monthly_energy`` and then again
with data ``YEARLY`` and output ``annual_energy``.

=======  ==============================
Key      Description
=======  ==============================
formula  name of a function
args     dictionary of data and outputs
returns  name of outputs
=======  ==============================

Dynamic Calculations
````````````````````
Dynamic calculations depend on a previous timestep. To refer to arguments from
previous timesteps use an index or to refer to a prior time use a quantity. In
the example below, encapsulant browning depends on the previous timestep and the
temperatures from the previous day. ::

    {
      "encapsulant_browning": {
        "formula": "f_encapsulant_browning",
        "args": {
          "data": {"encapsulant": "encapsulant"},
          "outputs": {
            "prev_encapsulant_browning": ["encapsulant_browning", -1],
            "prev_day_cell_temp": ["Tcell", -1, "day"]
          }
        },
        "returns": ["encapsulant_browning"]
      }
    }

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

Just like the :class:`~carousel.core.outputs.Output` class, we tell Carousel
about our calculations by specifying the parameter file in a
:class:`~carousel.core.calculations.Calc` class. Create a new Python module
in the pvpower package called ``performance.py``, like we did above and add a
:class:`~carousel.core.calculations.Calc` class for each calculation. ::

    from carousel.core.calculations import Calc
    import os
    from pvpower import PROJ_PATH


    class UtilityCalcs(Calc):
        outputs_file = 'utils.json'
        outputs_path = os.path.join(PROJ_PATH, 'calculations')

