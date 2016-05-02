.. _tutorial-2:

Tutorial 2
==========
The next step in FlyingCircus is to write calculations. In the second tutorial
we will create a calculation JSON parameter file and a
:class:`flying_circus.core.calculations.Calc` class for the PV power example.

Calculations
------------
Calculations are combined to make a simulation of a model. Calculations are
created in JSON parameter files and list the formulas and arguments that result
in outputs. Calculations can also have attributes like frequency and
`dependencies <http://xkcd.com/754/>`_. Calculation attributes are stored in the
calculation registry.

============  ============================================
Attribute     Description
============  ============================================
dependencies  list of required calculations
always_calc   calculations day and night
frequency     dynamic calculations different from timestep
static        list of one time calculations
dynamic       list of periodic calculations
============  ============================================

Static and Dynamic Calculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Both static and dynamic calculations are lists that describe the steps required
to calculate the desired outputs. Each step is a dictionary that contains keys
for ``formula``, ``args`` and ``returns``. The value of each key is a reference
to the value in the corresponding registry. Formulas can be used with different
arguments to return different outputs by referring to different values in the
data and output registries respectively.

=======  ==============================
Key      Description
=======  ==============================
formula  name of a function
args     dictionary of data and outputs
returns  name of outputs
=======  ==============================

For example create ``PVPower/calculations/performance.json``::

    {
      "static": [
        {
          "formula": "f_dc_power",
          "args": {
            "data": {"module": "PVModule"},
            "output": {
              "poa_direct": "Ibeam", "poa_diffuse": "Idiff",
              "cell_temp": "Tcell", "am_abs": "AM", "aoi": "AOI"
            }
          },
          "returns": ["Isc", "Imp", "Voc", "Vmp", "Pmp", "Ee"]
        },
        {
          "formula": "f_ac_power",
          "args": {
            "data": {"inverter": "PVInverter"},
            "output": {"v_mp": "Vmp", "p_mp": "Pmp"}
          },
          "returns": ["Pac"]
        }
      ]
    }


Dynamic Calculations
````````````````````
Dynamic calculations depend on a previous timestep. The simulation performs all
static calculations once, then marches time over all dynamic calculations. To
refer to arguments from previous timesteps use an index or to refer to a prior
time use a quantity. In the example below, encapsulant browning depends on the
previous timestep and the temperatures from the previous day.

Example calculate encapsulant browning::

    {
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

Calculation Class
-----------------
Just like the :class:`~flying_circus.core.outputs.Output` class, we tell
FlyingCircus about our calculations by specifying the parameter file in a
:class:`~flying_circus.core.calculations.Calc` class. Create a new Python module
in the pvpower package called ``calculations.py`` and add a
:class:`~flying_circus.core.calculations.Calc` class for each calculation. ::

    from flying_circus.core.calculations import Calc
    import os
    from pvpower import PROJ_PATH


    class UtilityCalcs(Calc):
        outputs_file = 'utils.json'
        outputs_path = os.path.join(PROJ_PATH, 'calculations')


    class PVerformanceCalcs(Calc):
        outputs_file = 'performance.json'
        outputs_path = os.path.join(PROJ_PATH, 'calculations')

Alternate method
~~~~~~~~~~~~~~~~
Instead of specifying the calculations in a parameter file, you can also specify
the calculations attributes directly in the class. ::

    from flying_circus.core.calculations import Calc


    class UtilityCalcs(Calc):
        dependencies = ["performance"]
        static = [
            {
                "formula": "f_energy",
                "args": {
                    "outputs": {"ac_power": "Pac",
                                "timeseries": "timeseries"}
                },
                "returns": ["hourly_energy", "hourly_timeseries"]
            },
            {
                "formula": "f_rollup",
                "args": {
                    "data": {"freq": "months"},
                    "outputs": {"items": "hourly_energy",
                                "timeseries": "hourly_timeseries"}
                },
                "returns": ["monthly_energy"]
            }
        ]


    class PVerformanceCalcs(Calc):
        static = [
            {
                "formula": "f_dc_power",
                "args": {
                    "data": {"module": "module"},
                    "output": {
                        "poa_direct": "Ibeam", "poa_diffuse": "Idiff",
                        "cell_temp": "Tcell", "am_abs": "AM", "aoi": "AOI"
                    }
                },
                "returns": ["Isc", "Imp", "Voc", "Vmp", "Pmp", "Ee"]
            },
            {
                "formula": "f_ac_power",
                "args": {
                    "data": {"inverter": "inverter"},
                    "output": {"v_mp": "Vmp", "p_mp": "Pmp"}
                },
                "returns": ["Pac"]
            }
        ]

Either method works, but you can't combine them in a single class.
