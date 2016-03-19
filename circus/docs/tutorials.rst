.. _tutorials:

Tutorials
=========

PV System Power Example
-----------------------
This example demonstrates using a external library to simulate a PV System.

Outputs
~~~~~~~
The first step in Circus is to decide what the desired outputs of the simulation
should be. Create output configuration files for each calculation in the
``outputs`` folder of the project. Use JSON to list the desired outputs and
their attributes.

Example ``PVPower/outputs/pvpower.json``::

    {
      "HourlyEnergy": {"units": "W*h", "init": 0, "size": 8760},
      "MonthlyEnergy": {"units": "W*h", "init": 0, "size": 12},
      "AnnualEnergy": {"units": "W*h", "init": 0}
    }

Output Attributes
+++++++++++++++++
Attributes, such as units, initial value and size, describe outputs.

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
