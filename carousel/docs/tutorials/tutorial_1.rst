.. _tutorial-1:

Tutorial 1: Outputs
===================
One of the first steps in modeling is to decide what the desired outputs should
be. For example, the outputs of a PV power simulation might be hourly energy and
the corresponding timestamps. In this tutorial we'll demonstrate how to specify
the outputs for a Carousel model. We use the term *outputs* to refer to the
results from calculations. We'll explain what the term *calculations* refers to
in :ref:`the next tutorial <tutorial-2>`, and we'll define the term *models* in
:ref:`the last tutorial <tutorial-5>`.

As discussed in :ref:`getting-started` there are two styles for specifying
Carousel parameters. First we'll show how to specify the output parameters
directly in an output subclass since this is the preferred method. Later we will
also show how to specify output parameters in a JSON file.

We'll need to create a new Python module inside the ``pvpower`` package created
by running ``carousel-quickstart``. We can actually define all of our Carousel
parameters in this file. Let's call the new module ``performance.py``. Inside
the new module, we'll have to import the :class:`~carousel.core.outputs.Output`
class so we can create a subclass to hold our output specifications. To specify
hourly energy, the corresponding timestamps and some other outputs for the PV
power performance model, copy the following snippet into the new module::

    """
    PV power performance simulation
    """

    from carousel.core.outputs import Output


    class PVPowerOutputs(Output):
        """
        Outputs for PV Power demo
        """
        timestamps = {"isconstant": True, "size": 8761}
        hourly_energy = {
            "isconstant": True, "timeseries": "hourly_timeseries",
            "units": "W*h",
            "size": 8760
        }
        hourly_timeseries = {"isconstant": True, "units": "W*h", "size": 8760}
        monthly_energy = {"isconstant": True, "units": "W*h", "size": 12}
        annual_energy = {"isconstant": True, "units": "W*h"}


Output Attributes
~~~~~~~~~~~~~~~~~
In the snippet each output is a class attribute defined by a dictionary of
properties. Outputs are described by attributes, such as units, initial value and size. The
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
To tell Carousel to use these outputs, now we need to open the ``pvpower``
package, create a new Python module called ``outputs.py`` and specify the file
and path to the JSON parameter file. ::

    from carousel.core.outputs import Output
    import os
    from pvpower import PROJ_PATH


    class PVPowerOutputs(Output):
        outputs_file = 'pvpower.json'
        outputs_path = os.path.join(PROJ_PATH, 'outputs')

Alternate Paradigm
~~~~~~~~~~~~~~~~~~
There are currently two paradigms for specifying outputs: either in a JSON
parameter file whos path is specified in a corresponding
:class:`carousel.core.outputs.Output` class or as class attributes
initiated with a dictionary of attributes in a corresponding
:class:`carousel.core.outputs.Output` class. The following example will
demonstrate the JSON parameter file paradigm.

The example above demonstrates the JSON parameter file paradigm. The alternate
paradigm is to specify the outputs directly in the Output class as
dictionaries. ::

    from carousel.core.outputs import Output


    class OutputsSourceTest2(Output):
        hourly_energy = {"units": "W*h", "init": 0, "size": 8760}
        monthly_energy = {"units": "W*h", "init": 0, "size": 12}
        annual_energy = {"units": "W*h", "init": 0}

Only one paradigm can me used for each Output class, but both methods do the
same thing.

One convenient way to organize outputs is We need to specify output parameters for
each calculation in the ``outputs`` folder of the project. Use JSON to list the
desired outputs and their attributes. Carousel uses this configuration to
create a memory key-store subclassed from dictionary called a registry. There is
a registry for each layer in Carousel subclassed from the base registry
class named after the layer.

For example create ``PVPower/outputs/pvpower.json``::

    {
      "hourly_energy": {"units": "W*h", "init": 0, "size": 8760},
      "monthly_energy": {"units": "W*h", "init": 0, "size": 12},
      "annual_energy": {"units": "W*h", "init": 0}
    }


