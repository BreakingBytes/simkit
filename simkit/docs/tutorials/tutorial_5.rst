.. _tutorial-5:

Tutorial 5: Models and Simulations
==================================
The PV system power demo now has all of the component except the simulation
and the model. The :class:`~simkit.core.simulations.Simulation` class defines
the parameters used to run the simulation. Simulation parameters are settings
that control the simulation. The :class:`~simkit.core.models.Model` class
collects all of the model components together. The two classes work closely with
each other because by default the simulation class is set as the command layer
in the model. Commands can be executed from the model by passing the name of the
command to the model :meth:`~simkit.core.models.Model.command` method.

Simulation Class
----------------
The simulation is delegated the responsibility of running the model. It is the
default command layer of the model meaning that commands passed to the model
execute methods in the simulation of the same name. The simulation layer also
stores any simulation or model settings such as the timestep, any thresholds
that limit when calculations are skipped and which data and output fields are
displayed or written while a dynamic simulation is running. A simulation can
have multiple sets of settings, each declared as a class attributes set to an
instance of :class:`~simkit.core.simulations.SimParameter`, but only one set
of settings are stored in the :class:`~simkit.core.simulations.SimRegistry`.
Much more on that later. For now here's the PV system power simulation example::

    from simkit.core.simulations import Simulation, SimParameter


    class PVPowerSim(Simulation):
        """
        PV Power Demo Simulations
        """
        settings = SimParameter(
            ID = "Tuscon_SAPM",
            path = "~/SimKit_Simulations",
            thresholds = None,
            interval = [1, "hour"],
            sim_length = [0, "hours"],
            write_frequency = 0,
            write_fields = {
                "data": ["latitude", "longitude", "Tamb", "Uwind"],
                "outputs": ["monthly_energy", "annual_energy"]
            },
            display_frequency = 12,
            display_fields = {
                "data": ["latitude", "longitude", "Tamb", "Uwind"],
                "outputs": ["monthly_energy", "annual_energy"]
            },
            commands = ['start', 'pause']
        )

Simulation Attributes
---------------------
The simulation parameter arguments correspond to attributes. If passed as
positional arguments, the order is given in the table below, otherwise keyword
arguments can be in any order.

===================  ============================================  =======
Attribute            Description                                   Default
===================  ============================================  =======
ID                   name used to save files
path                 location where files are saved
commands             list of methods that can be called by model
data                 *not used*
thresholds           list of limits when calculations are skipped  None
interval             length of timesteps for dynamic calculations  1-hour
sim_length           length of dynamic simulation                  1-year
display_frequency    frequency data displays in console            1
display_fields       data and output fields displayed in console   None
write_frequency      frequency that outputs written to file        8760
write_fields         data and outputs written in output file       None
===================  ============================================  =======

Defaults
~~~~~~~~
Most of the simulation settings are optional and apply specifically to dynamic
simulations only. If ID is not given then it will be generated from the
simulation class name and the date and time. The ID is used as the name for the
folder where files are written, and as a prefix of the files written. Each file
ends with a number to indicate the order. The default path of the folder where
the files are written from dynamic simulations is ``~/SimKit/Simulations``.
The default commands are ``'start'`` and ``'pause'``, but this list is only used
to populate the model :meth:`~simkit.core.models.Model.commands` property. The
data attribute is not used. The rest of the defaults are specified in the table.

Write and Display Fields
~~~~~~~~~~~~~~~~~~~~~~~~
The write and display fields determine what data and outputs are displayed or
written to disk during dynamic simulations. They should be set to a dictionary
containing two keys::

    ``{'data': ['list', 'of', 'data'], 'output': ['outputs', 'list']}``

The display and write frequency are in units of the interval, so if using the
default values then display is shown every 1 hour and written to disk every 8760
hours.

.. warning::
   Currently for static only simulations, the value for ``sim_length`` should be
   changed to ``[0, 'hour']`` and the write fields should be set to at least one
   data or outputs item, or the simulation will raise an unhandled exception.

Settings
--------
Settings are specified in the model by passing the ``settings`` argument to the
simulation model parameter. If no settings are provided, then the 1st setting is
used. However, more than one simulation class can be listed in the model, each
with it's own setting, so that's a workaround if multiple settings are desired.
To indicate which simulation to use, append the simulation, or list of
simulations after the command passed to the model. For example::

    m = MyModel()
    m.command('start MySimulation')  # runs MySimulation
    m.command('start')  # runs all simulations in the model
    m.command('start Sim1 Sim2 Sim3')  # starts Sim1, then Sim2, etc.

Model Class
-----------
The model class lists the user defined outputs, calculations, formulas, data and
simulations that make up a complete model as class attributes named after the
layer they represent. Subclass :class:`~simkit.core.models.Model` and list
each layer as an instance of :class:`~simkit.core.models.ModelParameter`. Pass
the classes you've defined for each layer as a list of ``sources`` and set the
the ``Meta`` class option ``modelpath`` to ``PROJ_PATH`` which is automatically
generated by ``simkit-quickstart`` in your model package. If a class takes an
argument then list that class as a tuple with the class first and the arguments
in a dictionary second. The model already has a map to the classes used to read
each layer, but you can optionally specify the ``layer`` argument. ::

    from pvpower import PROJ_PATH
    from simkit.core.models import Model


    class NewSAPM(Model):
        """
        PV Power Demo model
        """
        data = ModelParameter(
            layer = 'Data',
            sources = [(PVPowerData, {'filename': 'Tuscon.json'})]
        )
        outputs = ModelParameter(
            layer = 'Outputs',
            sources = [PVPowerOutputs, PerformanceOutputs, IrradianceOutputs]
        )
        formulas = ModelParameter(
            layer = 'Formulas',
            sources = [UtilityFormulas, PerformanceFormulas, IrradianceFormulas]
        )
        calculations = ModelParameter(
            layer = 'Calculations',
            sources = [UtilityCalcs, PerformanceCalcs, IrradianceCalcs]
        )
        simulations = ModelParameter(layer='Simulations', sources=[PVPowerSim])

        class Meta:
            modelpath = PROJ_PATH  # folder containing project, not model


Model Parameter Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~
The only argument that model parameters really need is a list of sources, but if
you need to you can also pass others. The order of positional arguments is the
same as the table, or you can pass keyword arguments in any order.

=========  ==========================================================
Attribute  Description
=========  ==========================================================
layer      name of the layer class of these parameters, optional
module     module that the sources are defined in, optional
package    package that the sources' module is contained in, optional
path       path to source package if not on ``PYTHONPATH``, optional
sources    name of classes with each layers parameters
=========  ==========================================================

Passing Arguments
~~~~~~~~~~~~~~~~~
Model parameters that take arguments such as the data and simulation layers can
be specified as a tuple. For example, if we want to load a specific set of data
for ``PVPowerData``, like Tuscon data, then we could declare it in the model. ::

    data = [(PVPowerData, {'filename': 'Tuscon.json'})]

Model Path
~~~~~~~~~~
The ``modelpath`` is an attribute that is used with the folder structure that is
created by ``simkit-quickstart``. You should set this to the ``PROJ_PATH``
module constant created in your project package by ``simkit-quickstart``.
It's confusing since the attribute is *model path* not *project path*, but
refers to the path that contains the layer folders created by
``simkit-quickstart``. The value of ``modelpath`` is prepended to the name of
the layer to set the relative path to look for files loaded by each
:class:`~simkit.core.layers.Layer`. For new parameter style models this is
actually only used by the data layer, since the model looks in the project
*data* folder created by ``simkit-quickstart``, unless ``path`` is passed as a
``sources`` argument, then it appends the value of ``path`` to the relative
path. So, still confused? Just set ``modelpath`` to the name of the folder
containing the *data* folder, which should be ``PROJ_PATH`` if you used
``simkit-quickstart``, and you'll be okay.

Running Model Simulation
------------------------
Finally, let's simulate the model. First import your model::

    >>> from pvpower.sandia_perfmod_newstyle import NewSAPM

Then, instantiate the model::

    >>> m = NewSAPM()

You can tell whether or not all of the layers are loaded in the model by
checking its state::

    >>> m.state  # returns 'initialized'

If the model layers: outputs, calculations, formulas, data and simulations are
not all initialized, then the state is "uninitialized".

The simulations commands are listed in the model as ``m.commands`` and tell you
which actions have been delegated to the command layer. In the PV system power
example, data is already loaded and we can now run the simulation of the model
with the start command.

    >>> m.command('start')

In cases where data has not been preloaded in the model, the base simulation
class ``run`` method first loads the specified data and then starts the
simulation.

    >>> m.command('run', data={'PVPowerData': {'filename': 'data/Tuscon.json'}})

This is equivalent to calling those two commands consecutively. The model data
cannot be reloaded without clearing it from the registry first or you will get a
:class:`~simkit.core.exceptions.DuplicateRegItemError` that indicates which
fields exist already. ::

    >>> m.command(
        'load', data={'PVPowerData': {'filename': 'data/Tuscon.json'}}
    ... )

    DuplicateRegItemError: Duplicate data can't be registered:
            YEARLY
            HOURLY
            inverter_database
            timestamp_count
            elevation
            Tamb
            inverter
            surface_azimuth
            module
            MONTHLY
            timestamp_start
            longitude
            Uwind
            module_database
            latitude
            timezone

The simulation has several properties that can be accessed directly from the
object, for example to see if data is already loaded::

    >>> m.simulations.objects['PVPowerSim'].is_data_loaded  # True


Registries
----------
All model parameters are stored in registries, which are a subclass of
dictionary. The are collected in the model for easy access. To get an output
you can access it by its keyname.

>>> annual_energy = sum(m.registries['outputs']['annual_energy']).to('kWh')
>>> print annual_energy  # 258.8441299 kilowatt_hour
