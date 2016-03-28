# -*- coding: utf-8 -*-
"""
This is the Circus core package. It contains the modules and configuration
files that form the core of Circus. Circus is extensible through its built-in
classes; therefore adding new data, formulas, calculations, simulation
solvers or output reports is accomplished by sub-classing the appropriate
class.

The built-in classes are organized into 5 sections, which make up the layers
of a model.

* Data
* Formulas
* Calculations
* Simulations
* Outputs

See the :ref:`dev-intro` in the developer section for more information on each
section.
"""

#import quantities as pq
import pint
import os
from inspect import getargspec
import json
import numpy as np

from circus.core.circus_exceptions import DuplicateRegItemError, \
    MismatchRegMetaKeysError

# add extra units to registry
UREG = pint.UnitRegistry()  # registry of units
Q_ = UREG.Quantity
UREG.define('lumen = cd * sr = lm')
UREG.define('lux = lumen / m ** 2 = lx')

# constants
YEAR = 2013 * UREG.year
_DIRNAME = os.path.dirname(__file__)
_DATA = os.path.join(_DIRNAME, '..', 'data')
_FORMULAS = os.path.join(_DIRNAME, '..', 'formulas')
_CALCS = os.path.join(_DIRNAME, '..', 'calcs')
_MODELS = os.path.join(_DIRNAME, '..', 'models')
_OUTPUTS = os.path.join(_DIRNAME, '..', 'outputs')
_SIMULATIONS = os.path.join(_DIRNAME, '..', 'simulations')


def _listify(x):
    """
    If x is not a list, make it a list.
    """
    return list(x) if isinstance(x, (list, tuple)) else [x]


class Registry(dict):
    """
    Base class for a registry.

    The register method can be used to add new keys to the registry only if
    they don't already exist. A registry can also have meta data associated
    with subsets of the registered keys. To enforce rules on meta when the keys
    are registered, override the register method and raise exceptions before
    calling the :func:`super` built-in function.

    By default there are no meta attributes, only the register method.
    To set meta attributes, in a subclass, add them in the constructor::

        def __init__(self):
            self.meta1 = {}
            self.meta2 = {}
            ...
    """
    def __init__(self):
        if hasattr(self, '_meta_names'):
            self._meta_names = _listify(self._meta_names)
            if [m for m in self._meta_names if m.startswith('_')]:
                raise AttributeError('No underscores in meta names.')
            for m in self._meta_names:
                # check for m in cls and bases
                if m in dir(Registry):
                    msg = ('Class %s already has %s member.' %
                           (self.__class__.__name__, m))
                    raise AttributeError(msg)
        super(Registry, self).__init__()

    def register(self, newitems, *args, **kwargs):
        """
        Register newitems in registry.

        :param newitems: New items to add to registry. When registering new
            items, keys are not allowed to override existing keys in the
            registry.
        :type newitems: mapping
        :param args: Key-value pairs of meta-data. The key is the meta-name,
            and the value is a map of the corresponding meta-data for new
            item-keys. Each set of meta-keys must be a subset of new item-keys.
        :type args: tuple or list
        :param kwargs: Maps of corresponding meta for new keys. Each set of
            meta keys must be a subset of the new item keys.
        :type kwargs: mapping
        :raises: :exc:`~circus_exceptions.DuplicateRegItemError`,
            :exc:`~circus_exceptions.MismatchRegMetaKeysError`
        """
        newkeys = newitems.viewkeys()  # set of the new item keys
        if any(self.viewkeys() & newkeys):  # duplicates
            raise DuplicateRegItemError(self.viewkeys() & newkeys)
        self.update(newitems)  # register new item
        # update meta fields
        if any(isinstance(_, dict) for _ in args):
            # don't allow kwargs to passed as args!
            raise TypeError('*args should be all named tuples.')
        # combine the meta args and kwargs together
        kwargs.update(args)  # doesn't work for combo of dicts and tuples
        for k, v in kwargs.iteritems():
            meta = getattr(self, k)  # get the meta attribute
            if v:
                if not v.viewkeys() <= newkeys:
                    raise MismatchRegMetaKeysError(newkeys - v.viewkeys())
                meta.update(v)  # register meta
        # TODO: default "tag" meta field for all registries?
        # TODO: append "meta" to all meta fields, so they're easier to find?

    def unregister(self, items):
        """
        Remove items from registry.

        :param items:
        """
        items = _listify(items)
        # get all members of Registry except private, special or class
        meta_names = (m for m in vars(self).iterkeys()
                      if (not m.startswith('_') and m not in dir(Registry)))
        # check that meta names matches
        # FIXME: this is so lame. replace this with something more robust
        for m in meta_names:
            if m not in self._meta_names:
                raise AttributeError('Meta name %s not listed.')
        # pop items from Registry and from meta
        for it in items:
            if it in self:
                self.pop(it)
            for m in (getattr(self, m_) for m_ in self._meta_names):
                if it in m:
                    m.pop(it)


# decorator to use with formulas to convert argument units
def convert_args(test_fcn, *test_args):
    """
    Decorator to be using in formulas to convert ``test_args`` depending on
    the ``test_fcn``.

    :param testfcn: A test function that converts arguments.
    :type testfcn: function
    :param test_args: Names of args to convert using ``test_fcn``.
    :type test_args: str

    The following test functions are available.
    * :func:`Kelvin_to_Celsius`
    * :func:`Celsius_to_Kelvin`
    * :func:`dimensionless_to_index`

    Example: Convert ``dawn_idx`` and ``eve_idx`` to indices::

        @convert_args(dimensionless_to_index, 'dawn_idx', 'eve_idx')
        def f_max_T(Tcell24, dawn_idx, eve_idx):
            idx = dawn_idx + np.argmax(Tcell24[dawn_idx:eve_idx])
            return Tcell24[idx], idx
    """
    def wrapper(origfcn):
        def newfcn(*args, **kwargs):
            argspec = getargspec(origfcn)  # use ``inspect`` to get arg names
            kwargs.update(dict(zip(argspec.args, args)))  # convert args to kw
            # loop over test args
            for a in test_args:
                # convert a if it's in args
                if a in argspec.args:
                    kwargs.update({a: test_fcn(kwargs[a])})  # update kwargs
            # call original function with converted args
            return origfcn(**kwargs)
        # copy original function special props to decorator for Sphinx
        newfcn.__doc__ = origfcn.__doc__  # copy docstring
        newfcn.__name__ = origfcn.__name__  # copy name
        # return wrapped function
        return newfcn
    # return the wrapper function that consumes the original function
    return wrapper

# NOTE: Preferred way to compare units is with dimensionality
# (25 * pq.degC).dimensionality == pq.degC.dimensionality
# NOTE: Another way to compare units as string is with name or symbol
# (25 * pq.degC).dimensionality.string == pq.degC.name
# (25 * pq.degC).dimensionality.string == pq.degC.symbol


def Kelvin_to_Celsius(temperature):
    # convert temperature from Kelvin to degC
    if temperature.dimensionality == pq.K.dimensionality:
        temperature = (temperature.magnitude - 273.15) * pq.degC
    elif temperature.dimensionality != pq.degC.dimensionality:
        raise Exception('Temperature units must be Kelvin or Celsius')
    # TODO: make an exception called TemperatureUnitsError
    return temperature


def Celsius_to_Kelvin(temperature):
    # convert temperature from degC to Kelvin
    if temperature.dimensionality == pq.degC.dimensionality:
        temperature = (temperature.magnitude + 273.15) * pq.K
    elif temperature.dimensionality != pq.K.dimensionality:
        raise Exception('Temperature units must be Kelvin or Celsius.')
    # TODO: make an exception called TemperatureUnitsError
    return temperature


def dimensionless_to_index(index):
    # convert dimensionless to index
    if index.dimensionality == UREG['dimensionless'].dimensionality:
        index = index.item()
    else:
        raise Exception('Indices must be dimensionless.')
    # TODO: make an exception called IndexUnitsError
    return index


# custom JSON encoder to serialize Quantities and NumPy arrays
class PV_JSONEncoder(json.JSONEncoder):
    def default(self, o):
        """
        JSONEncoder default method that converts NumPy arrays and quantities
        objects to lists.
        """
        if isinstance(o, pq.Quantity):
            return o.magnitude
        elif isinstance(o, np.ndarray):
            return o.tolist()
        else:
            # raise TypeError if not serializable
            return super(PV_JSONEncoder, self).default(o)


__all__ = []
