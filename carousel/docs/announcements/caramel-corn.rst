.. _caramel_corn:

Caramel Corn (v0.3.1)
=====================
This version is a *major* release with several new features which will break
previous Carousel models.

Parameters
~~~~~~~~~~
Starting with Carousel-0.3, all layers now use a ``Parameter`` class to
differentiate model parameters such as data, outputs, formulas, calculations,
simulations and models, from user defined class attributes which should not be
interpreted by Carousel. This affects some layers differently, specifically the
:class:`~carousel.core.formulas.Formula` and
:class:`~carousel.core.calculations.Calc` classes should now split formulas and
calculations into different ``Parameter`` objects instead of grouping them
together into one dictionary or list.

Data Source
+++++++++++
The easiest way to migrate data sources is to wrap the existing dictionary for
each data in a :class:`~carousel.core.data_sources.DataParameter` object::

    from carousel.core.data_sources import DataSource, DataParameter


    class PVPowerData(DataSource):
        """
        Data sources for PV Power demo.
        """
        # new v0.3
        latitude = DataParameter(units="degrees", uncertainty=1.0)

        # old v0.2.7
        # latitude = {"units": "degrees", "uncertainty": 1.0}

        # migration workaround just splat the dictionary inside a DataParameter
        # latitude = DataParameter(**{"units": "degrees", "uncertainty": 1.0})

        # user attribute
        user_attr = 'user attribute that should not be interpreted by Carousel'

For more information on data sources see :ref:`tutorial-4` and the API section
on :ref:`data-sources`.
