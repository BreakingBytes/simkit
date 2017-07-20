.. _tutorial-5:

Tutorial 5: Models and Simulations
==================================
The PV system power demo now has all of the component except simulation. The
:class:`carousel.core.simulations.Simulation` class defines the parameters used
to run the simulation. The :class:`carousel.core.models.Model` class collects
all of the model components together. The two classes work closely with each
other because by default the simulation class is set as the command layer in the
model.

Simulation Class
----------------
The simulation is delegated the responsibility of running the model. It also
stores any simulation or model settings such as the timestep, any thresholds
that limit when calculations are skipped and which data and output fields are
displayed or written while the simulation is running. The simulation class is
also unique in that its parameters can be set by passing the settings directly
as arguments in addition to declaring them as class attributes. Here's the PV
system power example::

    from carousel.core.simulations import Simulation


    class PVPowerSim(Simulation):
        """
        PV Power Demo Simulations
        """
        settings = SimParameter(
            ID="Tuscon_SAPM",
            path="~/Carousel_Simulations",
            thresholds=None,
            interval=[1, "hour"],
            sim_length=[0, "hours"],
            write_frequency=0,
            write_fields={
                "data": ["latitude", "longitude", "Tamb", "Uwind"],
                "outputs": ["monthly_energy", "annual_energy"]
            },
            display_frequency=12,
            display_fields={
                "data": ["latitude", "longitude", "Tamb", "Uwind"],
                "outputs": ["monthly_energy", "annual_energy"]
            },
            commands=['start', 'pause']
        )

Simulation Attributes
---------------------
The simulation arguments correspond to attributes.

===================  ============================================
Attribute            Description
===================  ============================================
ID                   name used to save files
path                 location where files are saved
thresholds           list of limits when calculations are skipped
interval             length of timesteps for dynamic calculations
sim_length           length of dynamic simulation
write_frequency      frequency that outputs written to file
write_fields         data and outputs written in output file
display_frequency    frequency data displays in console
display_fields       data and output fields displayed in console
commands             list of methods that can be called by model
===================  ============================================

Model Class
-----------
The model class lists the user defined outputs, calculations, formulas, data and
simulations that make up a complete model. ::

    from pvpower import PROJ_PATH
    from carousel.core.models import Model


    class NewSAPM(Model):
        """
        PV Power Demo model
        """
        data = ModelParameter(
            layer='Data', sources=[(PVPowerData, {'filename': 'Tuscon.json'})]
        )
        outputs = ModelParameter(
            layer='Outputs',
            sources=[PVPowerOutputs, PerformanceOutputs, IrradianceOutputs]
        )
        formulas = ModelParameter(
            layer='Formulas',
            sources=[UtilityFormulas, PerformanceFormulas, IrradianceFormulas]
        )
        calculations = ModelParameter(
            layer='Calculations',
            sources=[UtilityCalcs, PerformanceCalcs, IrradianceCalcs]
        )
        simulations = ModelParameter(layer='Simulations', sources=[PVPowerSim])

        class Meta:
            modelpath = PROJ_PATH  # folder containing project, not model

Model attributes that take arguments such as the data and simulation layers can
be specified as a tuple. For example, if we want to load a specific set of data
for ``PVPowerData``, like Tuscon data, then we could declare it in the model. ::

    data = [(PVPowerData, {'filename': 'Tuscon.json'})]

The ``modelpath`` is a legacy attribute that is used with the folder structure
that is created by ``carousel-quickstart``. For models created using the new
style in a single module, set ``modelpath = os.path.dirname(__file__)``.

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
example, data is already loaded and we can now run the simulation of the model with the start command.

    >>> m.command('start')

In cases where data has not been preloaded in the model, the base simulation class run method first loads the specified data and then starts the simulation.

    >>> m.command('run', data={'PVPowerData': {'filename': 'data/Tuscon.json'}})

It is equivalent to calling those two commands consecutively. The model data cannot be reloaded without clearing it from the registry first or you will get a
:class:`carousel.core.exceptions.DuplicateRegItemError` that indicates which
fields exist already. ::

    >>> m.command('load', data={'PVPowerData': {'filename': 'data/Tuscon.json'}})

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
