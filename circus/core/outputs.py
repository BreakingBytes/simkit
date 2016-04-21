# -*- coding: utf-8 -*-

"""
This module provides the framework for output data from Circus. It is very
similar to the data layer, except that output sources are always calculation
modes.
"""

from circus.core import Registry, UREG, Q_
import json
import numpy as np
import os


class OutputRegistry(Registry):
    """
    A registry for output data from calculations.
    """
    def __init__(self):
        super(OutputRegistry, self).__init__()
        #: initial value
        self.initial_value = {}
        #: size
        self.size = {}
        #: uncertainty
        self.uncertainty = {}
        #: ``True`` for each data-key if constant, ``False`` if periodic
        self.isconstant = {}
        #: ``True`` if each data-key is a material property
        self.isproperty = {}

    def register(self, new_outputs, init_val, size, unc, isconst, isprop):
        # TODO: check meta-data???
        # call super method
        kwargs = {'initial_value': init_val, 'size': size,
                  'uncertainty': unc, 'isconstant': isconst,
                  'isproperty': isprop}
        super(OutputRegistry, self).register(new_outputs, **kwargs)


class MetaOutputSource(type):
    """
    Meta class for user specified output source.

    Setting the ``__metaclass__`` attribute to :class:`MetaUserOutputSource`
    sets :class:`OutputSources` as the base class, forms the full path to the
    specified output file on the specified output path and passes it to the
    constructor as the `param_file` argument.

    Classes must set class attributes `output_path` and `output_file` to the
    specified output path and file.

    Example::

        class OutputSource(object):
            __metaclass__ = MetaUserOutputSource
            output_path = 'user_output_folder'
            output_file = 'new_user_output_source_param_file.json'

    It's not necessary to subclass :class:`object` is because it is already
    subclassed by :class:`DataSource`. All bases of :class:`DataSource` will be
    removed from bases before adding DataSource, so that.
    """
    def __new__(cls, name, bases, attr):
        # use only with OutputSources
        has_parents = [b for b in bases if isinstance(b, MetaOutputSource)]
        if not has_parents:
            return super(MetaOutputSource, cls).__new__(cls, name, bases, attr)
        outputs_path = attr.pop('outputs_path', None)
        outputs_file = attr.pop('outputs_file', None)
        if None not in [outputs_path, outputs_file]:
            attr['param_file'] = os.path.join(outputs_path, outputs_file)
        else:
            attr['parameters'] = dict.fromkeys(k for k in attr.iterkeys()
                                               if not k.startswith('_'))
            for k in attr['parameters'].iterkeys():
                attr['parameters'][k] = attr.pop(k)
        return super(MetaOutputSource, cls).__new__(cls, name, bases, attr)


class OutputSources(object):
    """
    A class for formating output sources.

    :param param_file: A configuration file containing the format for the
        output source.
    :type param_file: str
    """
    __metaclass__ = MetaOutputSource

    def __init__(self):
        #: parameter file
        if hasattr(self, 'param_file'):
            with open(self.param_file, 'r') as fp:
                #: parameters from file for outputs
                self.parameters = json.load(fp)
        #: outputs initial value
        self.initial_value = {}
        #: size of outputs
        self.size = {}
        #: outputs uncertainty
        self.uncertainty = {}
        #: outputs isconstant flag
        self.isconstant = {}
        #: outputs isproperty flag
        self.isproperty = {}
        #: (deg mode) calculation outputs
        self.outputs = {}
        for k, v in self.parameters.iteritems():
            self.initial_value[k] = v.get('init')  # returns None if missing
            self.size[k] = v.get('size') or 1  # minimum size is 1
            self.uncertainty[k] = None  # uncertainty for outputs is calculated
            self.isconstant[k] = v.get('isconstant', False)  # True or False
            self.isproperty[k] = v.get('isproperty', False)  # True or False
            units = str(v.get('units', ''))  # default is non-dimensional
            # NOTE: np.empty is faster than zeros!
            self.outputs[k] = Q_(np.zeros((1, self.size[k])), UREG[units])
            # NOTE: Initial values are assigned and outputs resized when
            # simulation "start" method is called from the model.


# TODO: create a fields module with a Field base class (and MetaField if necessary)
# TODO: create an OutputField class for outputs with attributes initial_value,
# size, uncertainty, isconstant, isproperty and the value.
# TODO: use OutputField instead of dictionaries
# TODO: just combine Outputs with other layers in Model class like Django