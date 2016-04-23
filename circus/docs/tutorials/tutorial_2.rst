.. _tutorial-2:

Tutorial 2
==========

Calculations
------------
The next step in Circus is to write calculations. Calculations are created in
configuration files as JSON and list the formulas and arguments that result in
outputs. Calculations can also have attributes like frequency and
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

Example create ``PVPower/calculations/pvpower.json``::

    {
      "static": [
        {
          "formula": "f_dc_power",
          "args": {
            "data": {"module": "module"},
            "output": {
              "poa_direct": "pos_direct", "poa_diffuse": "poa_diffuse",
              "cell_temp": "cell_temp", "am_abs": "am_abs", "aoi": "aoi"
            }
          },
          "returns": ["Isc", "Imp", "Voc", "Vmp", "Pmp", "Ee"]
        },
        {
          "formula": "f_ac_power",
          "args": {
            "data": {"inverter": "inverter"},
            "output": {"Vmp": "v_mp", "Pmp": "p_mp"}
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

