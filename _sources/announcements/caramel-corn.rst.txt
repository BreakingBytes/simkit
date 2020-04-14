.. _caramel_corn:

Caramel Corn CONSTANTS (v0.3.1)
===============================
This version is a *major* release with several new features which will break
previous SimKit models. In particular, the following new features have been
introduced starting with v0.3:

* ``Parameter`` classes instead of dictionaries are used to differentiate user
  attributes from parameter declarations.
* Use of ``Meta`` class options.
* ``Calculator`` base class that can be overriden by user to modify how
  calculations are performed.
* Separation of calculations into individual parameters that are all considered
  in the DAG.
* Separation of formulas into individual parameters.
* Introduction of simulation settings, which are instances of ``SimParameter``,
  and the ability to have multiple settings per simulation.

Pint-0.8 Incompatibility
------------------------
Unfortunately the newest version of Pint is not compatible with SimKit. This
is a known issue, and you can track its resolution on GitHub. Until the issue is
resolved please downgrade to Pint-0.7.2.

Parameters
----------
Starting with SimKit-0.3, all layers now use a ``Parameter`` class to
differentiate model parameters such as data, outputs, formulas, calculations,
simulations and models, from user defined class attributes which should not be
interpreted by SimKit. This affects some layers differently, specifically the
:class:`~simkit.core.formulas.Formula` and
:class:`~simkit.core.calculations.Calc` classes should now split formulas and
calculations into different ``Parameter`` objects instead of grouping them
together into one dictionary or list.

Migration Workarounds
~~~~~~~~~~~~~~~~~~~~~
The goal of these changes were to make SimKit classes easier to write and more
flexible because they allow user defined attributes to be used arbitrarily. Here
are some workarounds to help migrate v0.2.7 models to v0.3.

Outputs and Data Sources
++++++++++++++++++++++++
The easiest way to migrate outputs and data sources is to wrap the existing
dictionary for each data or output in either a
:class:`~simkit.core.data_sources.DataParameter` or
:class:`~simkit.core.outputs.OutputParameter` object and use a double star
operator, ``**``, to splat the dictionary into keyword arguments::

    from simkit.core.data_sources import DataSource, DataParameter


    class PVPowerData(DataSource):
        """
        Data sources for PV Power demo.
        """
        # old v0.2.7
        # latitude = {"units": "degrees", "uncertainty": 1.0}

        # migration workaround just splat dictionary inside DataParameter

        # new v0.3
        latitude = DataParameter(
            **{"units": "degrees", "uncertainty": 1.0}
        )
        # splat dictionary is equivalent to using keyword arguments
        # latitude = DataParameter(units="degrees", uncertainty=1.0)

        # user attribute, not a parameter
        user_attr = 'user attributes are now OK in v0.3'

For more information on data sources see :ref:`tutorial-4` and the API section
on :ref:`data-sources`. And for more information on outputs see
:ref:`tutorial-1` and the API section on :ref:`outputs`.

Formulas
++++++++
The only way to migrate formulas is to split them into individual parameters and
put the module and package attributes into a nested ``Meta`` class::

    from simkit.core.formulas import Formula, FormulaParameter


    class UtilityFormulas(Formula):
        """
        Formulas for PV Power demo
        """
        # old v0.2.7
        # formulas = {
        #     "f_energy": {
        #         "args": ["ac_power", "times"],
        #         "units": [["watt_hour", None], ["W", None]]
        #     },
        #     "f_rollup": {
        #         "args": ["items", "times", "freq"],
        #         "units": ["=A", ["=A", None, None]]
        #     }
        # }
        # module = ".utils"
        # package = "formulas"

        # migration workaround split formulas into separate parameters
        # and put package and module attributes into nested Meta class

        # new v0.3
        f_energy = FormulaParameter(
            args=["ac_power", "times"],
            units=[["watt_hour", None], ["W", None]]
        )
        f_rollup = FormulaParameter(
            args=["items", "times", "freq"],
            units=["=A", ["=A", None, None]]
        )
        class Meta:
            module = ".utils"
            package = "formulas"

        # user attribute, not a parameter
        user_attr = 'user attributes are now OK in v0.3'

For more information on formulas see :ref:`tutorial-3` and the API section
on :ref:`formulas`.

Calculations
++++++++++++
There is no easy workaround for migrating calculations to v0.3. Each calculation
will need to be split up into separate parameters, each parameter now has an
``is_dynamic`` attribute, can require its own dependencies as list of other
calculation parameters by name, and can also specify other options like
``always_calc`` or ``frequency``. Also, since calculation parameters are now
individually declared as ``Calculation`` class attributes, and not part of the
*old* ``static`` and ``dynamic`` calculation lists, calculation parameters now
need individual names. ::

    from simkit.core.calculations import Calc, CalcParameter, Calculator

    class UtilityCalcs(Calc):
        """
        Calculations for PV Power demo
        """
        # old v0.2.7
        # dependencies = ["PerformanceCalcs"]
        # static = [
        #     {
        #         "formula": "f_energy",
        #         "args": {
        #             "outputs": {"ac_power": "Pac", "times": "timestamps"}
        #         },
        #         "returns": ["hourly_energy", "hourly_timeseries"]
        #     },
        #     {
        #         "formula": "f_rollup",
        #         "args": {
        #             "data": {"freq": "MONTHLY"},
        #             "outputs": {"items": "hourly_energy",
        #                         "times": "hourly_timeseries"}
        #         },
        #         "returns": ["monthly_energy"]
        #     },
        #     {
        #         "formula": "f_rollup",
        #         "args": {
        #             "data": {"freq": "YEARLY"},
        #             "outputs": {"items": "hourly_energy",
        #                         "times": "hourly_timeseries"}
        #         },
        #         "returns": ["annual_energy"]
        #     }
        # ]

        # no easy migration workaround split calculations into separate
        # parameters, replace static/dynamic lists with is_dynamic attribute
        # put default options in Meta class, override new Calculator class to
        # change how calculations are performed

        # new v0.3
        energy = CalcParameter(
            dependencies=["ac_power", "daterange"],
            formula="f_energy",
            args={"outputs": {"ac_power": "Pac", "times": "timestamps"}},
            returns=["hourly_energy", "hourly_timeseries"]
        )
        monthly_rollup = CalcParameter(
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
            dependencies=["energy"],
            formula="f_rollup",
            args={"data": {"freq": "YEARLY"},
                  "outputs": {"items": "hourly_energy",
                              "times": "hourly_timeseries"}},
            returns=["annual_energy"]
        )
        class Meta:
            is_dynamic = False
            calculator = Calculator

For more information on calculations see :ref:`tutorial-2` and the API section
on :ref:`calculations`.

Static and Dynamic
``````````````````
In v0.3, static and dynamic calculations are now determined by each parameter's
``is_dynamic`` attribute, which defaults to ``False`` if not given. Therefore
there is no ``static`` or ``dynamic`` list of serial calculations, and the
calculation class does not have static and dynamic class attributes anymore.

Dependencies
````````````
Since calculation parameter names can be listed in the dependencies of other
calculation parameters, when the order of calculations is determined in the
simulation layer, each calculation parameter is now considered separately
instead of as a group of serial steps, as in v0.2.7. This means that SimKit
now has more granular control to determine which calculations can be performed
in parallel.

A default set of dependencies for all parameters in the calculation can be
listed as a ``Meta`` class option. If an individual parameter is missing the
``dependencies`` keyword, then the default is used from the ``Meta`` class.

Calculation ``Meta`` Class Options
``````````````````````````````````
Other calculation options like ``always_calc`` and ``frequency`` are also now
listed in a ``Meta`` class. If not specified individually in the calculation
parameter, then the value from the ``Meta`` class is used.

Calculator Class
````````````````
Another significant change for calculations is that individual calculations can
now specify a calculator class. A default calculator for all calculation
parameters can also be specified in the ``Meta`` class. A calculator is a new
base class that implements a ``calculate`` method but can be overriden to change
how calculations are performed. If not given then the default calculator for all
calculation parameters is the base ``Calculator`` class.

Simulations
+++++++++++
Migrating simulations is easy. Just take all of the class properties and drop
them into an instance of ``SimParameter``, which can be named anything you want,
but represents a set of settings you can use to simulate the model. Therefore,
you could potentially have more than one set of settings by defining more than
one ``SimParameter``. By default the first ``SimParameter`` is used for settings
if not specified in the model when declaring the model layers. ::

    from simkit.core.simulations import Simulation, SimParameter


    class PVPowerSim(Simulation):
        """
        PV Power Demo Simulations
        """
        # old v0.2.7
        # ID = "Tuscon_SAPM"
        # path = "~/SimKit_Simulations"
        # thresholds = None
        # interval = [1, "hour"]
        # sim_length = [0, "hours"]
        # write_frequency = 0
        # write_fields = {
        #     "data": ["latitude", "longitude", "Tamb", "Uwind"],
        #     "outputs": [
        #         "monthly_energy", "annual_energy"
        #     ]
        # }
        # display_frequency = 12
        # display_fields = {
        #     "data": ["latitude", "longitude", "Tamb", "Uwind"],
        #     "outputs": [
        #         "monthly_energy", "annual_energy"
        #     ]
        # }
        # commands = ['start', 'pause', 'run', 'load']

        # new v0.3
        settings = SimParameter(
            ID="Tuscon_SAPM",
            path="~/SimKit_Simulations",
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

For more information on simulations see :ref:`tutorial-5` and the API section
on :ref:`simulations`.

Models
++++++
Migrating models to v0.3 is also straightforward. Just take all of the layers
and declare them by name as ``ModelParameters``. The value of each layer is
given as the ``source`` keyword argument of the ``ModelParameter``. The
``modelpath`` should be in the model's ``Meta`` class. Instead of using the
default map of layers to ``Layer`` classes, if desired optionally provide the
name of the ``Layer`` class as the ``layer`` keyword argument for each
``ModelParameter``. ::

    from pvpower import PROJ_PATH
    from simkit.core.models import Model, ModelParameter

    class NewSAPM(Model):
        """
        PV Power Demo model
        """
        # old v0.2.7
        # modelpath = PROJ_PATH  # folder containing project, not model
        # data = [PVPowerData]
        # outputs = [PVPowerOutputs, PerformanceOutputs, IrradianceOutputs]
        # formulas = [UtilityFormulas, PerformanceFormulas, IrradianceFormulas]
        # calculations = [UtilityCalcs, PerformanceCalcs, IrradianceCalcs]
        # simulations = [PVPowerSim]

        # new v0.3
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

For more information on models see :ref:`tutorial-5` and the API section on
:ref:`models`.

Meta Class Options
----------------------
Another major change is that any SimKit class options that aren't parameters
should now be put in a nested class called ``Meta``. This should be familiar to
Django, SQLAlchemy and Marshmallow users, and in fact much of SimKit is
heavily inspired by those other projects.
