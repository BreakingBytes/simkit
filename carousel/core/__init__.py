# -*- coding: utf-8 -*-
"""
This is the Carousel core package. Carousel is extensible through its
built-in classes; therefore adding new data sources, formulas importers,
calculators, simulations is accomplished by sub-classing the appropriate
class.

The built-in classes are organized into 5 categories, which make up the layers
of a model.

* Data
* Formulas
* Calculations
* Simulations
* Outputs

See the :ref:`dev-intro` in the developer section for more information on each
section.
"""

import pint
import os
from inspect import getargspec
import functools
import json
import numpy as np
import warnings
import logging
from carousel.core.exceptions import (
    DuplicateRegItemError, MismatchRegMetaKeysError
)

warnings.simplefilter('always', DeprecationWarning)
logging.captureWarnings(True)
# create default logger from root logger with debug level, stream handler and
# formatter with date-time, function name, line no and basic configuration
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
LOG_FORMAT = ('\n> %(asctime)s %(funcName)s:%(lineno)d\n> ' +
              '\n'.join(logging.BASIC_FORMAT.rsplit(':', 1)))
logging.basicConfig(datefmt=LOG_DATEFMT, format=LOG_FORMAT)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

# unit registry, quantity constructor and extra units registry definitions
UREG = pint.UnitRegistry()  # registry of units
Q_ = UREG.Quantity  # quantity constructor for ambiguous quantities like degC
UREG.define('lumen = cd * sr = lm')
UREG.define('lux = lumen / m ** 2.0 = lx')
UREG.define('fraction = []')  # define new dimensionless base unit for percents
UREG.define('percent = fraction / 100.0 = pct')  # can't use "%" only ascii
UREG.define('suns = []')  # dimensionless unit equivalent to 1000.0 [W/m/m]

# define PV solar context
_PV = pint.Context('pv')
# define transformation of suns to power flux and vice versa
E0 = 1000.0 * UREG.W / UREG.m / UREG.m  # 1 sun
_PV.add_transformation('[]', '[power] / [area]', lambda ureg, x: x * E0)
_PV.add_transformation('[power] / [area]', '[]', lambda ureg, x: x / E0)
UREG.add_context(_PV)


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
        if hasattr(self, 'meta_names'):
            self.meta_names = _listify(self.meta_names)
            if [m for m in self.meta_names if m.startswith('_')]:
                raise AttributeError('No underscores in meta names.')
            for m in self.meta_names:
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
        :raises:
            :exc:`~carousel.core.exceptions.DuplicateRegItemError`,
            :exc:`~carousel.core.exceptions.MismatchRegMetaKeysError`
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
            if m not in self.meta_names:
                raise AttributeError('Meta name %s not listed.')
        # pop items from Registry and from meta
        for it in items:
            if it in self:
                self.pop(it)
            for m in (getattr(self, m_) for m_ in self.meta_names):
                if it in m:
                    m.pop(it)


# decorator to use with formulas to convert argument units
def convert_args(test_fcn, *test_args):
    """
    Decorator to be using in formulas to convert ``test_args`` depending on
    the ``test_fcn``.

    :param test_fcn: A test function that converts arguments.
    :type test_fcn: function
    :param test_args: Names of args to convert using ``test_fcn``.
    :type test_args: str

    The following test functions are available.
    * :func:`dimensionless_to_index`

    Example: Convert ``dawn_idx`` and ``eve_idx`` to indices::

        @convert_args(dimensionless_to_index, 'dawn_idx', 'eve_idx')
        def f_max_T(Tcell24, dawn_idx, eve_idx):
            idx = dawn_idx + np.argmax(Tcell24[dawn_idx:eve_idx])
            return Tcell24[idx], idx
    """
    def wrapper(origfcn):
        @functools.wraps(origfcn)
        def newfcn(*args, **kwargs):
            argspec = getargspec(origfcn)  # use ``inspect`` to get arg names
            kwargs.update(zip(argspec.args, args))  # convert args to kw
            # loop over test args
            for a in test_args:
                # convert a if it's in args
                if a in argspec.args:
                    kwargs[a] = test_fcn(kwargs[a])  # update kwargs
            # call original function with converted args
            return origfcn(**kwargs)
        # return wrapped function
        return newfcn
    # return the wrapper function that consumes the original function
    return wrapper

# NOTE: Preferred way to compare units is with dimensionality
# EG: (25 * UREG.degC).dimensionality == UREG.degC.dimensionality
# XXX: Really? because this works too, seems way better!
# EG: (25 * UREG.degC).units = UREG.degC


def dimensionless_to_index(index):
    # convert dimensionless to index
    if not index.dimensionality:
        index = index.magnitude
    else:
        raise TypeError('Indices must be dimensionless.')
    # TODO: make an exception called IndexUnitsError
    return index


# custom JSON encoder to serialize Quantities and NumPy arrays
class CarouselJSONEncoder(json.JSONEncoder):
    def default(self, o):
        """
        JSONEncoder default method that converts NumPy arrays and quantities
        objects to lists.
        """
        if isinstance(o, Q_):
            return o.magnitude
        elif isinstance(o, np.ndarray):
            return o.tolist()
        else:
            # raise TypeError if not serializable
            return super(CarouselJSONEncoder, self).default(o)


class CommonBase(type):
    """
    Provides common metaclass methods.

    * :meth:`get_parents` ensures initialization only from subclasses of the
      main class and not the main class itself
    * :meth:`set_param_file_or_parameters` adds class attributes ``param_file``
      or ``parameters`` depending on whether the path and file of the parameters
      are given or if the parameters are listed as class attributes.

    Base classes must implement the ``_path_attr`` and ``_file_attr`` as class
    attributes::

        class ExampleBase(CommonBase):
            _path_attr = 'outputs_path'  # class attribute with parameter path
            _file_attr = 'outputs_file'  # class attribute with parameter file
    """
    _path_attr = NotImplemented
    _file_attr = NotImplemented

    @classmethod
    def set_param_file_or_parameters(mcs, attr):
        cls_path = attr.pop(mcs._path_attr, None)
        cls_file = attr.pop(mcs._file_attr, None)
        # TODO: read parameters from param_file and then also update from attr
        if None not in [cls_path, cls_file]:
            attr['param_file'] = os.path.join(cls_path, cls_file)
        else:
            attr['parameters'] = dict.fromkeys(
                k for k in attr if not k.startswith('_')
            )
            for k in attr['parameters']:
                attr['parameters'][k] = attr.pop(k)
        return attr

    @staticmethod
    def get_parents(bases, parent):
        """
        Ensures that initialization only performed on subclasses of parent
        https://github.com/django/django/blob/master/django/db/models/base.py

        :param bases: Bases to compare against parent.
        :type bases: list
        :param parent: Superclass that bases should be subclassed from.
        :return: Bases subclassed from parent.
        :rtype: list
        """
        return [b for b in bases if isinstance(b, parent)]
