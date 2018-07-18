.. _dev-intro:

Developers
==========
The next few sections describe the API, developing models with SimKit and
making contributions.

Introduction
------------
SimKit is designed to be easily extensible. Adding new calculations,
formulas, data, outputs, simulations and models is standardized, facilitating
development by many users.

Layers
~~~~~~
The structure of SimKit is divided into five layers:

* Data
* Formulas
* Calculations
* Simulations
* Outputs

All five layers are combined to make a model. Data that the model uses is
handled by the **Data** layer. The **Formulas** layer takes care of all of the
formulas used in the **Calculations** layer. Data and formulas can be used in
more than one calculation. Outputs of calculations are handled by the
**Outputs** layer. Finally the **Simulations** layer handles running
simulations.

Registry
~~~~~~~~
All layers have a registry that collects all of the elements in that layer. The
registry serves several purposes.

* It restricts layer elements from being registered twice. Once an element is
  is registered, another element cannot be registered with the same name.
* It allows quick transfer of the layer and all of its elements from one part
  of the model to another. Calculations need access to formulas, data and
  outputs. And simulations need access to calculations.
* It allows meta information to be attached to elements in a layer. Data have
  values but also uncertainty, so a value is stored for each element in the
  data registry, but the data element's uncertainty is also stored as meta.

Model
~~~~~
The model loads and saves the layers, initializes and makes updates to layers,
validates itself and executes commands. There can be many SimKit models
with different combinations of layers and different commands. SimKit can
be extended with new variations subclassed from the base model and layer classes
to create new features and functionality.
