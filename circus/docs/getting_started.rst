.. _getting-started:

Getting Started
===============
Circus helps you build complicated models quickly. The quickstart and tutorials
that follow will guide you through the steps to making and simulating an example
Circus model.

.. _getting-started-quickstart:

Quickstart
----------
Circus adds the script ``circus-quickstart.py`` to quickly start a project. ::

    $ circus-quickstart.py MyCircusProject.

This creates a new folder for ``MyCircusProject`` with seven sub-folders. ::

    MyCircusProject
    |
    +-+- mycircusproject
    | |
    | +- __init__.py
    |
    +- models
    | |
    | +- default.json
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
Circus model. There are are five tutorials in the example.

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
Before creating a circus model, use ``circus-quickstart PVPower`` to create a
new project named ``PVPower`` with the following folders: ``pvpower``, ``data``,
``formulas``, ``calculations``, ``outputs``. ``simulations`` and ``models``.
The ``models`` folder contains a JSON file called ``default.json`` for the
default model. A Python package with the same name as the project in lower case
is used for data sources and readers, formulas sources, calculations, outputs,
simulations and models. In this demo, the project package is ``pvpower``. See
the :ref:`getting-started-quickstart` section in :ref:`getting-started` for more
info.

The next tutorial covers specifying outputs for your Circus model.
