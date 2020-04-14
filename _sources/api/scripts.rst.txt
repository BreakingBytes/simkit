.. _scripts:

Scripts
=======
SimKit installs the following scripts in the Python bin/scripts folder.

SimKit Quickstart
-------------------
.. py:module:: simkit-quickstart

Creates a basic file structure to start a SimKit project. ::

    Project
    |
    +-+- project
      |
      +- __init__.py
      |
      +- data

The contents of ``Project/project/__init__.py`` is the following::

    """
    This is the Project package.
    """

    import os

    __version__ = '0.1'
    __author__ = 'your name'
    __email__ = 'your.name@company.com'

    PROJ_PATH = os.path.abspath(os.path.dirname(__file__))

Call ``simkit-quickstart.py`` from the command line to see usage, help and
version information. Some more detail is also given in :ref:`getting-started`.
