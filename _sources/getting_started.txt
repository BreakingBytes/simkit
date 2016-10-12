.. _getting-started:

Getting Started
===============
Carousel helps you build complicated models quickly. The
:ref:`getting-started-quickstart` and :ref:`tutorials` that follow will guide
you through the steps to making and simulating an example Carousel model.

.. _getting-started-quickstart:

Quickstart
----------
Carousel adds the script :mod:`carousel-quickstart` to quickly start a
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

The quickstart script adds the constant ``mycarouselproject.PROJ_PATH`` that
refers to the project path ``MyCarouselProject/``. This path is useful, as we'll
see in the :ref:`next tutorial <tutorial-1>`, and should be imported into the
project package modules. The script also adds version, author and email
information that you can complete if you want. Finally a sample model parameter
file is created in ``MyCarouselProject/models/my_model.json`` - feel free to
delete this if not used. The sample parameter file is used in the legacy style
described in the :ref:`parameter-styles` section below.

.. _tutorials:

Tutorials
---------
The following :ref:`tutorials` will go through an example of how to implement a
Carousel model. There are are five tutorials that cover the different steps in
making a Carousel model.

* :ref:`Tutorial 1: Outputs <tutorial-1>`
* :ref:`Tutorial 2: Calculations <tutorial-2>`
* :ref:`Tutorial 3: Formulas <tutorial-3>`
* :ref:`Tutorial 4: Data Sources and Readers <tutorial-4>`
* :ref:`Tutorial 5: Models and Simulations <tutorial-5>`

PV System Power Example
~~~~~~~~~~~~~~~~~~~~~~~
The example in this tutorial demonstrates using a Python package called
`PVLIB <https://pypi.python.org/pypi/pvlib>`_ to simulate a photovoltaic (PV)
power system. It follows the example in the Package Overview section of the
PVLIB documentation. A working version of the demonstration model is included in
the ``examples`` folder of both the Carousel Git repository and the archive
distribution of the Carousel Python package.

Quickstart
~~~~~~~~~~
To start the tutorial, first execute ``carousel-quickstart PVPower`` from your
OS terminal (*EG*: BaSH on Linux, ``CMD`` on Windows). This will create a new
Carousel project named ``PVPower`` containing the following folders:
``pvpower``, ``data``, ``formulas``, ``calculations``, ``outputs``,
``simulations`` and ``models``. A Python package is created with the same name
as the project in lower case, *ie*: ``pvpower``, and a file called
``my_model.json`` is created in the ``models`` folder. These folders will be
used to create Carousel models in the tutorials that follow. For more
information about :mod:`carousel-quickstart` see the
:ref:`getting-started-quickstart` section in :ref:`getting-started`.

The :ref:`next tutorial <tutorial-1>` covers specifying outputs for your
Carousel model.

.. _parameter-styles:

Parameters
----------
Carousel currently has two different styles for entering model parameters. The
goal is to make entering model parameters intuitive, quick yet flexible.

Class Attributes
~~~~~~~~~~~~~~~~
Carousel allows most model parameters to be set as class attributes without
using `dunder <http://nedbatchelder.com/blog/200605/dunder.html>`_ classes such
as ``__init__``. This is the preferred way of specifying models in Carousel
because all of the code is Python and located in the fewest number of files.

JSON File
~~~~~~~~~
Originally Carousel collected all parameters from JSON files because it was
meant to be used entirely from a graphic user interface, therefore the
application state was saved and reloaded using JSON. This legacy style still
works in the current version of Carousel and can even be combined with the class
attribute style by specifying the parameter files as class attributes.

Class Instance Arguments
~~~~~~~~~~~~~~~~~~~~~~~~
Only models can be created by passing arguments to the
:class:`~carousel.core.models.Model` class constructor to instantiate the model.
Therefore models can be created three different ways.

1. Calling the model constructor with the model parameter file as the argument::

    m = models.Model('path/to/project/models/parameter_file.json')  # method # 1

2. Specifying the model parameters as class attributes::

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

3. Specifying the path to the model parameter file as class attributes::

    class MyModel(models.Model):
        """
        JSON parameter file specified as class attributes
        """
        modelpath = PROJ_PATH  # path to project folder
        modelfile = MODELFILE  # path to model parameter file in project/models

    m = MyModel()  # method # 3

