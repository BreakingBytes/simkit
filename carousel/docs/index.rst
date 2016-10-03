.. Carousel documentation master file, created by
   sphinx-quickstart on Wed Feb 10 14:16:34 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Carousel's documentation!
========================================

Version: |version| (|release|)

Announcements:
--------------

Parameter Files
~~~~~~~~~~~~~~~
Carousel now recommends using class attributes instead of JSON parameter files
to declare outputs, data, formulas, calculations, simulations and models.
Parameter files can still be used and there are currently no plans to deprecate
them.

Simulation File
~~~~~~~~~~~~~~~
The use of a simulation filename and path has been deprecated. If you use a
simulation filename and path in your model and you have enabled logging you
should see a ``DeprecationWarning``. The preferred style is to set simulation
parameters in your simulation class as class attributes.

Also the ``interval_length`` simulation attribute has been renamed to
``interval`` and ``simulation_length`` has been renamed to ``sim_length``, which
are the names that are used internally.

For more information on these changes and the simulation layer please see the
:ref:`Models and Simulations <tutorial-5>` tutorial.

Model Subclass
~~~~~~~~~~~~~~
The ``BaseModel`` subclass has been removed. Please use
:class:`~carousel.core.models.Model` instead.

Tutorials:
----------

.. toctree::
   :maxdepth: 2

   getting_started
   tutorials/tutorial_1
   tutorials/tutorial_2
   tutorials/tutorial_3
   tutorials/tutorial_4
   tutorials/tutorial_5


API:
----

.. toctree::
   :maxdepth: 2

   api/developer
   api/core
   api/outputs
   api/calculations
   api/simulations


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. include:: ../../README.rst
