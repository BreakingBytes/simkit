Circus - A Python Model Simulation Framework
============================================
Circus ia s framework for simulating mathematical models that decouples the
models from the simulation implementation. It takes care of boilerplate routines
such as loading data from various sources into a key store that can be used from
any calculation, determining the correct order of calculations, stepping through
dynamic simulations and generating output reports and visualizations, so that
you can focus on developing models and don't have to worry about how to add new
models or how to integrate changes.

Features
--------
* Built in integration of units and uncertainty.
* Built in management of input data, calculated outputs and formulas in simple
  keystore.
* Boilerplate designs for reading data from various sources.
* Automatic determination of calculation order.
* Boilerplate designs for progress display and output reports.
* All configuration files use human readable JSON serialization.

Requirements
------------
* [quantities](https://pythonhosted.org/quantities)
* [numpy](https://docs.scipy.org/doc/numpy/)
* [xlrd](http://pythonexcel.org)
* [nose](https://rtfd.org/nose/)
* [sphinx](https://sphinx-doc.org)

Installation
------------
You can use `pip` or `distutils` to install circus.

### [`pip`](http://pip.readthedocs.org/en/stable/)
    $ pip install circus

### [`disutils`](https://docs.python.org/2/install/)
    $ curl -Ok https://github.com/SunPower/Circus/archive/v0.1.tar.gz
    $ tar -xf v0.1.tar.gz
    $ cd Circus-0.2
    $ python setup.py install

Quickstart
----------
Circus adds the script `circus-quickstart.py` to quickly start a project.

    $ circus-quickstart.py MyCircusProject.

This creates a new folder for `MyCircusProject` with seven sub-folders.

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

Documentation
-------------
Circus documentation is online at https://sunpower.github.io/circus. It's also
included in the distribution and can be built by running the `Makefile` found
in the `docs` folder of the Circus package. Documentation uses Sphinx, and
built documentation will be found in the `_build` folder under the tree
corresponding to the type of documentation built; _EG_ HTML documentation is in
`docs/_build/html`.
