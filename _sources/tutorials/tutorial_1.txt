.. _tutorial-1:

Tutorial 1
==========

Outputs
-------
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
~~~~~~~~~~~~~~~~~
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
++++++++++++++++++++++
Outputs of dynamic calculations that represent a material property hold their
last value when the calculation is skipped. For example, soiling is an output
that is a material property. When soiling is not calculated, the accumulated
soiling is held at the last calculated value.

Constant Value Flag
+++++++++++++++++++
Constant values do not change during dynamic calculations.
