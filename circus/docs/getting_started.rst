.. _getting-started:

Getting Started
===============

Requirements
------------
* `quantities <https://pythonhosted.org/quantities>`_
* `numpy <https://docs.scipy.org/doc/numpy/>`_
* `xlrd <http://pythonexcel.org>`_
* `nose <https://rtfd.org/nose/>`_
* `sphinx <https://sphinx-doc.org>`_

Installation
------------
You can use `pip <http://pip.readthedocs.org/en/stable/>`_ or
`disutils <https://docs.python.org/2/install/>`_ to install circus. ::

    $ pip install circus

    $ curl -Ok https://github.com/SunPower/Circus/archive/v0.1.tar.gz
    $ tar -xf v0.1.tar.gz
    $ cd Circus-0.2
    $ python setup.py install

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
