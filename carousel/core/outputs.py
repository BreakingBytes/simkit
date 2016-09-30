# -*- coding: utf-8 -*-

"""
This module provides the framework for output from Carousel. It is similar
to the data layer except output sources are always calculations.
"""

from carousel.core import logging, CommonBase, UREG, Q_, Registry
import json
import numpy as np

LOGGER = logging.getLogger(__name__)


class OutputRegistry(Registry):
    """
    A registry for output from calculations.
    """
    meta_names = [
        'initial_value', 'size', 'uncertainty', 'variance', 'jacobian',
        'isconstant', 'isproperty', 'timeseries', 'output_source'
    ]

    def __init__(self):
        super(OutputRegistry, self).__init__()
        #: initial value
        self.initial_value = {}
        #: size
        self.size = {}
        #: uncertainty
        self.uncertainty = {}
        #: variance
        self.variance = {}
        #: jacobian
        self.jacobian = {}
        #: ``True`` for each output-key if constant, ``False`` if periodic
        self.isconstant = {}
        #: ``True`` if each output-key is a material property
        self.isproperty = {}
        #: name of corresponding time series output, ``None`` if no time series
        self.timeseries = {}
        #: name of :class:`Output` superclass
        self.output_source = {}

    def register(self, new_outputs, *args, **kwargs):
        kwargs.update(zip(self.meta_names, args))
        # call super method
        super(OutputRegistry, self).register(new_outputs, **kwargs)


class OutputBase(CommonBase):
    """
    Metaclass for outputs.

    Setting the ``__metaclass__`` attribute to :class:`OutputBase` adds the
    full path to the specified output parameter file as ``param_file`` or
    adds ``parameters`` with outputs specified. Also checks that outputs is a
    subclass of :class:`Output`. Sets `output_path` and `output_file` as the
    class attributes that specify the parameter file full path.
    """
    _path_attr = 'outputs_path'
    _file_attr = 'outputs_file'

    def __new__(mcs, name, bases, attr):
        # use only with Output subclasses
        if not CommonBase.get_parents(bases, OutputBase):
            return super(OutputBase, mcs).__new__(mcs, name, bases, attr)
        # set param file full path if outputs path and file specified or
        # try to set parameters from class attributes except private/magic
        attr = mcs.set_param_file_or_parameters(attr)
        return super(OutputBase, mcs).__new__(mcs, name, bases, attr)


class Output(object):
    """
    A class for formatting outputs.

    Do not use this class directly. Instead subclass it in your output model and
    list the path and file of the outputs parameters or provide the parameters
    as class members.

    Example of specified output parameter file::

        import os

        PROJ_PATH = os.path.join('project', 'path')  # project path


        class PVPowerOutputs(Output):
            outputs_file = 'pvpower.json'
            outputs_path = os.path.join(PROJ_PATH, 'outputs')

    Example of specified output parameters::

        class PVPowerOutputs(Output):
            hourly_energy = {'init': 0, 'units': 'Wh', 'size': 8760}
            yearly_energy = {'init': 0, 'units': 'kWh'}
    """
    __metaclass__ = OutputBase

    def __init__(self):
        if hasattr(self, 'param_file'):
            with open(self.param_file, 'r') as fp:
                #: parameters from file for outputs
                self.parameters = json.load(fp)
        else:
            #: parameter file
            self.param_file = None
        #: outputs initial value
        self.initial_value = {}
        #: size of outputs
        self.size = {}
        #: outputs uncertainty
        self.uncertainty = {}
        #: variance
        self.variance = {}
        #: jacobian
        self.jacobian = {}
        #: outputs isconstant flag
        self.isconstant = {}
        #: outputs isproperty flag
        self.isproperty = {}
        #: name of corresponding time series, ``None`` if no time series
        self.timeseries = {}
        #: name of :class:`Output` superclass
        self.output_source = {}
        #: calculation outputs
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
            self.timeseries[k] = v.get('timeseries')  # None if not time series
            self.output_source[k] = self.__class__.__name__  # output source


# TODO: create a fields module with a Field base class (MetaField if necessary)
# TODO: create an OutputField class for outputs with attributes initial_value,
# size, uncertainty, isconstant, isproperty and the value.
# TODO: use OutputField instead of dictionaries
# EG: hourly_energy = OutputField(init=0, units="W*h", size=8760)
# TODO: just combine Outputs with other layers in Model class like Django
