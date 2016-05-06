.. _getting-started:

Getting Started
===============
Carousel helps you build complicated models quickly. The
:ref:`getting-started-quickstart` and :ref:`tutorials` that follow will guide
you through the steps to making and simulating an example Carousel model.

.. _getting-started-quickstart:

Quickstart
----------
Carousel adds the script ``carousel-quickstart.py`` to quickly start a
project. ::

    $ carousel-quickstart.py MyCarouselProject.

This creates a new folder for ``MyCarouselProject`` with seven
sub-folders. ::

    MyCarouselProject
    |
    +-+- mycarouselproject
    | |
    | +- __init__.py
    |
    +- models
    | |
    | +- my_model.json
    |
    +- simulation
    |
    +- outputs
    |
    +- calculations
    |
    +- formulas
    |
    +- data

.. _tutorials:

Tutorials
---------
Next go through the example in the :ref:`tutorials` to implement your first
Carousel model. There are are five tutorials in the example.

* :ref:`Outputs <tutorial-1>`
* :ref:`Calculations <tutorial-2>`
* :ref:`Formulas <tutorial-2>`
* :ref:`Data Sources and Readers <tutorial-2>`
* :ref:`Models and Simulations <tutorial-2>`

PV System Power Example
~~~~~~~~~~~~~~~~~~~~~~~
This example demonstrates using a external library to simulate a PV System.
The `PVLIB <https://pypi.python.org/pypi/pvlib>`_ library is required for this
demonstration.

Quickstart
~~~~~~~~~~
Before creating a Carousel model, use ``carousel-quickstart PVPower``
to create a new project named ``PVPower`` with the following folders:
``pvpower``, ``data``, ``formulas``, ``calculations``, ``outputs``.
``simulations`` and ``models``. The ``models`` folder contains a JSON file
called ``my_model.json`` for your first model. A Python package with the same
name as the project in lower case is used for data sources and readers, formulas
sources, calculations, outputs, simulations and models. In this demo, the
project package is ``pvpower``. See the :ref:`getting-started-quickstart`
section in :ref:`getting-started` for more info.

The next tutorial covers specifying outputs for your Carousel model.
