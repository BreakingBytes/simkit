.. _brown-bicycle-bears:

Brown Bicycle Bears (v0.2.7)
============================
There are some important changes for this version that may break some Carousel
models.

Parameter Files
~~~~~~~~~~~~~~~
Carousel now recommends using class attributes instead of JSON parameter files
to declare outputs, data, formulas, calculations, simulations and models.
Parameter files can still be used and there are currently no plans to deprecate
them.

Simulation Filename
~~~~~~~~~~~~~~~~~~~
The use of a simulation filename and path has been deprecated. If you use a
simulation filename and path in your model and you have enabled logging you
should see a :exc:`exceptions.DeprecationWarning`. The preferred style is to
set simulation parameters in your simulation class as class attributes.

Also the ``interval_length`` simulation attribute has been renamed to
:attr:`~carousel.core.simulations.Simulation.interval` and ``simulation_length``
has been renamed to :attr:`~carousel.core.simulations.Simulation.sim_length`,
which are the names that are used internally.

For more information on these changes and the simulation layer please see the
:ref:`Models and Simulations <tutorial-5>` tutorial.

Model Subclass
~~~~~~~~~~~~~~
The ``BaseModel`` subclass has been removed. Please use
:class:`~carousel.core.models.Model` instead.