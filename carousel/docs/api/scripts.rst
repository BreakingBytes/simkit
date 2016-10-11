.. _scripts:

Scripts
=======
Carousel installs the following scripts in the Python bin/scripts folder.

Carousel Quickstart
-------------------
.. py:module:: carousel-quickstart

Creates a basic file structure to start a Carousel project. ::

    Project
    |
    +-+- project
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

The contents of ``project/__init__.py`` is the following::

    """
    This is the Project package.
    """

    import os

    __version__ = '0.1'
    __author__ = 'your name'
    __email__ = 'your.name@company.com'

    PKG_PATH = os.path.abspath(os.path.dirname(__file__))
    PROJ_PATH = os.path.dirname(PKG_PATH)

An empty model is contained in ``models/my_model.json``. ::

    {
      "outputs": null,
      "formulas": null,
      "data": null,
      "calculations": null,
      "simulations": null
    }

Call ``carousel-quickstart.py`` from the command line to see usage, help and
version information. Some more detail is also given in :ref:`getting-started`.
