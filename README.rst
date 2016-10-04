.. image:: https://travis-ci.org/SunPower/Carousel.svg?branch=master
    :target: https://travis-ci.org/SunPower/Carousel

Carousel - Model Simulation Framework
==================================================
Carousel ia a framework for simulating mathematical models that decouples
the models from the simulation implementation. It takes care of boilerplate
routines such as loading data from various sources into a key store that can be
used from any calculation, determining the correct order of calculations,
stepping through dynamic simulations and generating output reports and
visualizations, so that you can focus on developing models and don't have to
worry about how to add new models or how to integrate changes.

Features
--------
* Built in integration of units and uncertainty.
* Built in management of input data, calculated outputs and formulas in simple
  key store.
* Boilerplate designs for reading data from various sources.
* Automatic determination of calculation order.
* Boilerplate designs for progress display and output reports.
* All configuration files use human readable JSON serialization.

Requirements
------------
* `Pint <http://pint.readthedocs.org/en/latest/>`_
* `NumPy <http://www.numpy.org/>`_
* `xlrd <http://www.python-excel.org/>`_
* `nose <http://nose.readthedocs.org/en/latest/>`_
* `sphinx <https://sphinx-doc.org>`_
* `SciPy <http://www.scipy.org/scipylib/>`_
* `Python-Dateutil <https://dateutil.readthedocs.org/en/stable/>`_
* `UncertaintyWrapper <http://sunpower.github.io/UncertaintyWrapper/>`_

Installation
------------
Carousel `releases are on PyPI <https://pypi.python.org/pypi/Carousel>`_ and on
`GitHub <https://github.com/SunPower/Carousel/releases>`_. You can use either
``pip`` or ``distutils`` to install Carousel.

`pip <https://pip.pypa.io/en/stable/>`_ ::

    $ pip install Carousel

Extract the archive to use `disutils <https://docs.python.org/2/install/>`_ ::

    $ python setup.py install

Documentation
-------------
Carousel `documentation <https://sunpower.github.io/Carousel>`_ is
online. It's also included in the distribution and can be built by running the
``Makefile`` found in the ``docs`` folder of the Carousel package.
Documentation uses Sphinx, and built documentation will be found in the
``_build`` folder under the tree corresponding to the type of documentation
built. *EG*: HTML documentation is in ``docs/_build/html``.

Contributions
-------------
Carousel `source code <https://github.com/SunPower/Carousel>`_ is
online. Fork it and report
`issues <https://github.com/SunPower/Carousel/issues>`_, make suggestions or
create pull requests. Discuss the roadmap or download presentations on the
`wiki <https://github.com/SunPower/Carousel/wiki>`_

History
-------
The
`change log for all releases <https://github.com/SunPower/Carousel/releases>`_
is on GitHub.
