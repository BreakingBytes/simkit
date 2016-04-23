.. _tutorial-1:

Tutorial 1
==========
The first step in Circus is to decide what the desired outputs of the simulation
should be. Outputs are the result of calculations that are combined to make a
simulation. Create output configuration files for each calculation in the
``outputs`` folder of the project. Use JSON to list the desired outputs and
their attributes. Circus uses this configuration to create a memory key-store
subclassed from dictionary called a registry. There is a registry for each layer
in Circus subclassed from the base registry class named after the layer.

Outputs
-------
There are currently two paradigms for specifying outputs: either in a JSON
parameter file whos path is specified in a corresponding
:class:`circus.core.outputs.Output` class or as class attributes initiated with
a dictionary of attributes in a corresponding
:class:`circus.core.outputs.Output` class. The following example will
demonstrate the JSON parameter file paradigm.

For example create ``PVPower/outputs/pvpower.json``::

    {
      "hourly_energy": {"units": "W*h", "init": 0, "size": 8760},
      "monthly_energy": {"units": "W*h", "init": 0, "size": 12},
      "annual_energy": {"units": "W*h", "init": 0}
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

Outputs Class
-------------
To tell Circus to use these outputs, now we need to open the ``pvpower``
package, create a new Python module called ``outputs.py`` and specify the file
and path to the JSON parameter file. ::

    from circus.core.outputs import Output
    import os
    from pvpower import PROJ_PATH


    class PVPowerOutputs(Output):
        outputs_file = 'pvpower.json'
        outputs_path = os.path.join(PROJ_PATH, 'outputs')

Alternate Paradigm
~~~~~~~~~~~~~~~~~~
The example above demonstrates the JSON parameter file paradigm. The alternate
paradigm is to specify the outputs directly in the Output class as
dictionaries. ::

    from circus.core.outputs import Output


    class OutputsSourceTest2(Output):
        hourly_energy = {"units": "W*h", "init": 0, "size": 8760}
        monthly_energy = {"units": "W*h", "init": 0, "size": 12}
        annual_energy = {"units": "W*h", "init": 0}

Only one paradigm can me used for each Output class, but both methods have the
same outcome.
