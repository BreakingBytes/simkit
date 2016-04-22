.. _tutorials:

Tutorials
=========

PV System Power Example
-----------------------
This example demonstrates using a external library to simulate a PV System.
The `PVLIB <https://pypi.python.org/pypi/pvlib>`_ library is required for this
demonstration.


Quickstart
~~~~~~~~~~
Before creating a circus model, use ``circus-quickstart PVPower`` to create a
new project named ``PVPower`` with the following folders: ``pvpower``, ``data``,
``formulas``, ``calculations``, ``outputs``. ``simulations`` and ``models``.
The ``models`` folder contains a JSON file called ``default.json`` for the
default model. A Python package with the same name as the project in lower case
is used for data sources and readers, formulas sources, calculations, outputs,
simulations and models. In this demo, the project package is ``pvpower``. See
the :ref:`getting-started-quickstart` section in :ref:`getting-started` for more
info.

Outputs
~~~~~~~
The first step in Circus is to decide what the desired outputs of the simulation
should be. Outputs are the result of calculations that are combined to make a
simulation. Create output configuration files for each calculation in the
``outputs`` folder of the project. Use JSON to list the desired outputs and
their attributes. Circus uses this configuration to create a memory key-store
subclassed from dictionary called a registry. There is a registry for each layer
in Circus subclassed from the base registry class named after the layer.

Example create ``PVPower/outputs/pvpower.json``::

    {
      "HourlyEnergy": {"units": "W*h", "init": 0, "size": 8760},
      "MonthlyEnergy": {"units": "W*h", "init": 0, "size": 12},
      "AnnualEnergy": {"units": "W*h", "init": 0}
    }

Output Attributes
+++++++++++++++++
Outputs are described by attributes, such as units, initial value and size. The
output attributes are stored with the output values in the output registry.

==========  ========================
Attribute   Description
==========  ========================
units       output units
init        initial value
isproperty  material property flag
isconstant  constant value flag
size        array size
==========  ========================

Material Property Flag
``````````````````````
Outputs of dynamic calculations that represent a material property hold their
last value when the calculation is skipped. For example, soiling is an output
that is a material property. When soiling is not calculated, the accumulated
soiling is held at the last calculated value.

Constant Value Flag
```````````````````
Constant values do not change during dynamic calculations.

Calculations
~~~~~~~~~~~~
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
+++++++++++++++++++++++++++++++
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

