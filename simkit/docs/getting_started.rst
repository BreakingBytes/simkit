.. _getting-started:

Getting Started
===============
SimKit helps you build complicated models quickly. The
:ref:`getting-started-quickstart` and :ref:`tutorials` that follow will guide
you through the steps to making and simulating an example SimKit model.

.. _getting-started-quickstart:

Quickstart
----------
SimKit adds the script :mod:`simkit-quickstart` to quickly start a
project. ::

    $ simkit-quickstart.py MySimKitProject.

This creates a new folder for ``MySimKitProject``, a Python package with the
same name, and a *data* folder. ::

    MySimKitProject
    |
    +-+- mysimkitproject
      |
      +- __init__.py
      |
      +- data

The quickstart script adds the constant ``mysimkitproject.PROJ_PATH`` that
refers to the project path ``MySimKitProject/mysimkitproject``. This path is
useful, as we'll see in the :ref:`next tutorial <tutorial-1>`, and should be
imported into the project package modules. The script also adds version, author
and email information that you can complete if you want.

.. _tutorials:

Tutorials
---------
The following :ref:`tutorials` will go through an example of how to implement a
SimKit model. There are are five tutorials that cover the different steps in
making a SimKit model.

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
the ``examples`` folder of both the SimKit Git repository and the archive
distribution of the SimKit Python package.

Quickstart
~~~~~~~~~~
To start the tutorial, first execute ``simkit-quickstart PVPower`` from your
OS terminal (*EG*: BaSH on Linux, ``CMD`` on Windows). This will create a new
SimKit project named ``PVPower`` containing the following folders:
``pvpower``, ``data``, ``formulas``, ``calculations``, ``outputs``,
``simulations`` and ``models``. A Python package is created with the same name
as the project in lower case, *ie*: ``pvpower``, and a file called
``my_model.json`` is created in the ``models`` folder. These folders will be
used to create SimKit models in the tutorials that follow. For more
information about :mod:`simkit-quickstart` see the
:ref:`getting-started-quickstart` section in :ref:`getting-started`.

The :ref:`next tutorial <tutorial-1>` covers specifying outputs for your
SimKit model.

.. _parameter-styles:

Parameters
----------
Model parameters are items that are declared in each layer of a SimKit model.
For example a model's *data* layer might declare data parameters called
"direct_normal_irradiance" and "ambient_temperature" with attributes like
"units" and "uncertainty". SimKit's goal is to make entering model parameters
intuitive, quick yet flexible, so there are currently two different styles for
entering model parameters.

Class Attributes
~~~~~~~~~~~~~~~~
The preferred way to specify model parameters in each SimKit layer is to
declare them as class attributes equal to an instance of ``Parameter``. Each
SimKit class has its own ``Parameter`` class to set the items for that layer.
Behind the scenes SimKit collects parameters and instantiates them without
needing to write `dunder <http://nedbatchelder.com/blog/200605/dunder.html>`_
methods such as ``__init__``. Therefore model parameters are declared in a
simple and concise way. Please see the tutorials for examples.

JSON File
~~~~~~~~~
Originally SimKit collected all parameters from JSON files because it was
meant to be used entirely from a graphic user interface, therefore the
application state was saved and reloaded using JSON. This legacy style still
works in the current version of SimKit and can even be combined with the class
attribute style by specifying the parameter files as class ``Meta`` options.

Model Class Instance
~~~~~~~~~~~~~~~~~~~~
There is a third method for entering model parameters that can only be used when
creating a SimKit *model* directly from a model parameter JSON file by calling
:class:`~simkit.core.models.Model` with the filename as the argument.
Therefore SimKit *models* can be created three different ways.

1. Specifying the model parameters as class attributes of a subclass of
   :class:`~simkit.core.models.Model`::

    class MyModel(models.Model):
        """
        Layers specified as class attributes. This is the preferred way.
        """
        data = ModelParameter(
            layer='Data',
            sources=[(MyModelData, {'filename': 'data.json'}), ...]
        )
        outputs = ModelParameter(
            layer='Outputs', sources=[MyModelOutputs, ...]
        )
        formulas = ModelParameter(
            layer='Formulas', sources=[MyModelFormulas, ...]
        )
        calculations = ModelParameter(
            layer='Calculations', sources=[MyModelCalculations, ...]
        )
        simulations = ModelParameter(
            layer='Simulations', sources=[MyModelSimulations]
        )

        class Meta:
            modelpath = PROJ_PATH  # path to project folder

    m = MyModel()

2. Specifying the path to the model parameter file as ``Meta`` class
   options::

    class MyModel(models.Model):
        """
        JSON parameter file specified as ``Meta`` class options.
        """
        class Meta:
            modelpath = PROJ_PATH  # path to project folder
            modelfile = MODELFILE  # path to model parameter file

    m = MyModel()

3. Calling :class:`~simkit.core.models.Model` with the model parameter file as
   the argument::

    m = models.Model('path/to/project/models/parameter_file.json')

The SimKit *model* is the only class that can be instantiated directly by the
user. The other classes, *data*, *formulas*, *calculations*, *outputs*, and
*simulations*, are instantiated by the model class automatically.

Meta Class Options
------------------
Model options that apply to an entire SimKit class are listed separately in a
nested class that is always called ``Meta``. For each layer, there are a few
options that are typically listed in the ``Meta`` class. For example, the
*model* class has an attribute called ``modelpath`` that is listed in the
``Meta`` class and refers to the project path created by
``simkit-quickstart``. Please read the tutorials to learn more about what
``Meta`` class options can be used in each SimKit layer.
