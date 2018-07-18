.. _simulations:

Simulations
============
.. automodule:: simkit.core.simulations

Simulations Parameter
---------------------
.. autoclass:: SimParameter

   See :class:`Simulation` attributes for list of parameter arguments.

Simulations Registry
--------------------

.. autoclass:: SimRegistry

Simulations Base
----------------

.. autoclass:: SimBase

Simulations
-----------
.. autoclass:: Simulation
   :members:

   Attribute defaults are given in square brackets if not specified.

   .. py:attribute:: attrs

      class attributes and their defaults

   .. py:attribute:: ID

      ID for this particular simulation, used for path & file names, defaults to
      hyphenation of the class name and date/time in ISO format.

   .. py:attribute:: path

      path where SimKit simulation files are stored, defaults to
      `SimKit/Simulations` in the `$HOME` directory

   .. py:attribute:: commands

      list of commands corresponding to methods exposed to model, defaults to
      `['start', 'pause']`

   .. py:attribute:: data

      dictionary of batch data to simulate [`None`]

   .. py:attribute:: thresholds

      thresholds for dynamic calculations as a dictionary of maximum and minimum
      limits for each data, *eg*: `{'DNI': [0, 1400]}` will limit DNI between
      zero and the solar constant [`None`]

   .. py:attribute:: interval

      length of each interval [1-hour]

   .. py:attribute:: sim_length

      simulation length [1-year]

   .. py:attribute:: display_frequency

      frequency output is displayed, default is every interval

   .. py:attribute:: display_fields

      fields displayed, default is `None` which displays all fields

   .. py:attribute:: write_frequency

      frequency output is saved, default to
      :attr:`~simkit.core.simulations.Simulation.number_intervals`

   .. py:attribute:: write_fields

      fields written to disk, default is `None` which writes all fields
