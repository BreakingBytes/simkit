.. _caramel_corn:

Caramel Corn (v0.3.1)
=====================
This version is a *major* release with several new features which will break
previous Carousel models.

Parameters
----------
Starting with Carousel-0.3, all layers now use a ``Parameter`` class to
differentiate model parameters such as data, outputs, formulas, calculations,
simulations and models, from user defined class attributes which should not be
interpreted by Carousel. This affects some layers differently, specifically the
:class:`~carousel.core.formulas.Formula` and
:class:`~carousel.core.calculations.Calc` classes should now split formulas and
calculations into different ``Parameter`` objects instead of grouping them
together into one dictionary or list.

Migration Workarounds
~~~~~~~~~~~~~~~~~~~~~
There are some workarounds to help migrate v0.2.7 Carousel models to v0.3.

Outputs and Data Sources
++++++++++++++++++++++++
The easiest way to migrate outputs and data sources is to wrap the existing
dictionary for each data or output in either a
:class:`~carousel.core.data_sources.DataParameter` or
:class:`~carousel.core.outputs.OutputParameter` object and use a double star
operator, ``**``, to splat the dictionary into keyword arguments::

    from carousel.core.data_sources import DataSource, DataParameter


    class PVPowerData(DataSource):
        """
        Data sources for PV Power demo.
        """
        # old v0.2.7
        # latitude = {"units": "degrees", "uncertainty": 1.0}

        # migration workaround just splat dictionary inside DataParameter

        # new v0.3
        latitude = DataParameter(
            **{"units": "degrees", "uncertainty": 1.0}
        )
        # splat dictionary is equivalent to using keyword arguments
        # latitude = DataParameter(units="degrees", uncertainty=1.0)

        # user attribute, not a parameter
        user_attr = 'user attributes are now OK in v0.3'

For more information on data sources see :ref:`tutorial-4` and the API section
on :ref:`data-sources`. And for more information on outputs see
:ref:`tutorial-1` and the API section on :ref:`outputs`.

Formulas
++++++++
The only way to migrate formulas is to split them into individual parameters and
put the module and package attributes into a nested ``Meta`` class::

    from carousel.core.formulas import Formula, FormulaParameter


    class UtilityFormulas(Formula):
        """
        Formulas for PV Power demo
        """
        # old v0.2.7
        # formulas = {
        #     "f_energy": {
        #         "args": ["ac_power", "times"],
        #         "units": [["watt_hour", None], ["W", None]]
        #     },
        #     "f_rollup": {
        #         "args": ["items", "times", "freq"],
        #         "units": ["=A", ["=A", None, None]]
        #     }
        # }
        # module = ".utils"
        # package = "formulas"

        # migration workaround split formulas into separate parameters
        # and put package and module attributes into nested Meta class

        # new v0.3
        f_energy = FormulaParameter(
            args=["ac_power", "times"],
            units=[["watt_hour", None], ["W", None]]
        )
        f_rollup = FormulaParameter(
            args=["items", "times", "freq"],
            units=["=A", ["=A", None, None]]
        )
        class Meta:
            module = ".utils"
            package = "formulas"

        # user attribute, not a parameter
        user_attr = 'user attributes are now OK in v0.3'
