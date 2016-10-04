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
    +-+- models
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

* :ref:`Tutorial 1: Outputs <tutorial-1>`
* :ref:`Tutorial 2: Calculations <tutorial-2>`
* :ref:`Tutorial 3: Formulas <tutorial-3>`
* :ref:`Tutorial 4: Data Sources and Readers <tutorial-4>`
* :ref:`Tutorial 5: Models and Simulations <tutorial-5>`

PV System Power Example
~~~~~~~~~~~~~~~~~~~~~~~
This example demonstrates using a external library to simulate a photovoltaic
(PV) power system. The `PVLIB <https://pypi.python.org/pypi/pvlib>`_ library is
required for this demonstration.

Quickstart
~~~~~~~~~~
To start the tutorial, first execute ``carousel-quickstart PVPower`` from your
OS terminal (_EG_: BaSH on Linux, ``CMD`` on Windows). This will create a new
Carousel project named ``PVPower`` containing the following folders:
``pvpower``, ``data``, ``formulas``, ``calculations``, ``outputs``,
``simulations`` and ``models``. A Python package is created with the same name
as the project in lower case, _ie_: ``pvpower``, and a file called
``my_model.json`` is created in the ``models`` folder. These folders will be
used to create Carousel models in the tutorials that follow. For more
information about ``carousel-quicstart`` see the
:ref:`getting-started-quickstart` section in :ref:`getting-started`.

The :ref:`next tutorial <tutorial-1>` covers specifying outputs for your
Carousel model.

Parameters
----------
Carousel currently has several styles for entering model parameters. The goal is
to make entering model parameters intuitive, quick yet flexible.

Class Attributes
~~~~~~~~~~~~~~~~
Carousel allows most model parameters to be set as class attributes without
using `dunder <http://nedbatchelder.com/blog/200605/dunder.html>`_ classes such
as ``__init__``. This is the preferred way of specifying models in Carousel
because all of the code is Python and located in the fewest number of files.

JSON File
~~~~~~~~~
Originally Carousel collected all parameters from JSON files because it was
meant to be used entirely from graphic user interface, therefore the application
state was saved and reloaded using JSON. This legacy style still works in the
current version of Carousel and can even be combined with the class attribute
style by specifying the parameter files as class attributes.

Class Instance Arguments
~~~~~~~~~~~~~~~~~~~~~~~~
Only models can be created by passing arguments to the ``Model`` class
constructor to instantiate the model. Therefore models can be created three
different ways:

    m = MyModel('path/to/model/file.json')  # method # 1


    class MyModel(models.Model):
        """
        Layers specified as class attributes
        """
        data = [(MyModelData, {'filename': 'data.json'}), ...]
        outputs = [MyModelOutputs, ...]
        formulas = [MyModelFormulas, ...]
        calculations = [MyModelCalculations, ...]
        simulations = [MyModelSimulations]

    m = MyModel()  # method # 2 (preferred)


    class MyModel(models.Model):
        """
        JSON parameters specified as class attributes
        """
        modelpath = PROJ_PATH
        modelfile = MODELFILE

    m = MyModel()  # method # 2
