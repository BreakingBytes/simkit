Circus - A Python Model Simulation Framework
============================================
Circus ia s framework for developing simulations of mathematical models that
decouples your mathematical models from their computational implementations. It
takes care of boilerplate routines such as loading data from various sources
into a key store that can be used from any calculation, determining the correct
order of calculations, stepping through dynamic simulations and generating
output reports and visualizations, so that you can focus on developing models
and don't have to worry about how to add new models or how to implement changes.


Installation
------------
You can use `pip` or `distutils` to install circus.

### [`pip`](http://pip.readthedocs.org/en/stable/)
    $ pip install circus

### [`disutils`](https://docs.python.org/2/install/)
    $ curl -Ok https://github.com/SunPower/Circus/archive/v0.1.tar.gz
    $ tar -xf v0.1.tar.gz
    $ cd Circus-0.1
    $ python setup.py install

Quickstart
----------
Circus adds the script `circus-quickstart.py` to quickly start a project.

    $ circus-quickstart.py MyCircusProject.

This creates a new folder for `MyCircusProject` with five sub-folders.

    MyCircusProject
    |
    +-+- mycircusproject
    | |
    | +- __init__.py
    |
    +- models
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
