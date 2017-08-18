.. _carousel:

Carousel (v0.3.2)
=================

Quickstart
----------
The ``carousel-quickstart`` now only creates a *data* folder, and it puts the
*data* folder inside the project package. It doesn't create any other folders
explicitly, and it doesn't create a sample model parameter JSON file. There is
an option to create additional *layer* folders inside the project package.

The ``carousel-quickstart`` also now provides an option to initialize the
project as a Git repository. If found it will set the ``__author`` and
``__email__`` fields in the project package ``__init__.py`` file from either
the Git global configuration or from system environmental variables.

Setup Dulwich Requirement
-------------------------
Also, even though `Dulwich <https://www.dulwich.io/>`_ is now a requirement
in ``setup.py``, the ``carousel/__init__.py`` file now has a *try/except* block
around the ``dulwich`` import to make sure that installation goes smoothly.
