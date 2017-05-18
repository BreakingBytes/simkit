"""
Custom data readers including :class:`carousel.contrib.readers.ArgumentReader`,
:class:`carousel.contrib.readers.DjangoModelReader` and
:class:`carousel.contrib.readers.HDF5Reader`.
"""

import numpy as np
import h5py
from carousel.core.data_readers import DataReader
from carousel.core.data_sources import DataParameter
from carousel.core import Q_
import logging

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def copy_model_instance(obj):
    """
    Copy Django model instance as a dictionary excluding automatically created
    fields like an auto-generated sequence as a primary key or an auto-created
    many-to-one reverse relation.

    :param obj: Django model object
    :return: copy of model instance as dictionary
    """
    meta = getattr(obj, '_meta')  # make pycharm happy
    # dictionary of model values excluding auto created and related fields
    return {f.name: getattr(obj, f.name)
            for f in meta.get_fields(include_parents=False)
            if not f.auto_created}


# TODO: make parameters consistent for all readers
# TODO: parameters set by attributes in data source model fields
# EG: ghi = FloatField('GHI', units='W/m**2')
# EG: solar_azimuth = FloatField('solar azimuth', units='degrees')
# TODO: some parameters set in class Meta
# EG: class Meta: args = ['GHI', 'azimuth']

class ArgumentReader(DataReader):
    """
    Read arguments passed directly to a simulation.

    The argument parameters dictionary should have two keys: `args` and `kwargs`
    which consist of the names and attributes of the positional and keyword
    arguments respectively. For example::

        {
            'GHI': {'units': 'W/m**2', 'isconstant': False, 'argpos': 0},
            'azimuth': {'units': 'degrees', 'isconstant': False, 'argpos': 1},
            'DNI': {'units': 'W/m**2', 'isconstant': False},
            'zenith': {'units': 'degrees', 'isconstant': False}
        }

    """
    #: True if reader accepts ``filename`` argument
    is_file_reader = False  # not a file reader

    def load_data(self, *args, **kwargs):
        """
        Collects positional and keyword arguments into `data` and applies units.

        :return: data
        """
        # get positional argument names from parameters and apply them to args
        # update data with additional kwargs
        argpos = {
            v['extras']['argpos']: k for k, v in self.parameters.iteritems()
            if 'argpos' in v['extras']
        }
        data = dict(
            {argpos[n]: a for n, a in enumerate(args)}, **kwargs
        )
        return self.apply_units_to_cache(data)

    def apply_units_to_cache(self, data):
        """
        Applies units to data when a proxy reader is used. For example if the
        data is cached as JSON and retrieved using the
        :class:`~carousel.core.data_readers.JSONReader`, then units can be
        applied from the original parameter schema.

        :param data: Data read by proxy reader.
        :return: data with units applied
        """
        # if units key exists then apply
        for k, v in self.parameters.iteritems():
            if v and v.get('units'):
                data[k] = Q_(data[k], v.get('units'))
        return data


class DjangoModelReader(ArgumentReader):
    """
    Reads arguments that are Django objects or lists of objects.
    """
    def __init__(self, parameters=None, meta=None):
        #: Django model
        self.model = meta.model
        model_meta = getattr(self.model, '_meta')  # make pycharm happy
        # model fields excluding AutoFields and related fields like one-to-many
        all_model_fields = [
            f for f in model_meta.get_fields(include_parents=False)
            if not f.auto_created
        ]
        all_field_names = [f.name for f in all_model_fields]  # field names
        # use all fields if no parameters given
        if parameters is None:
            parameters = DataParameter.fromkeys(
                all_field_names, {}
            )
        fields = getattr(meta, 'fields', all_field_names)  # specified fields
        LOGGER.debug('fields:\n%r', fields)
        exclude = getattr(meta, 'exclude', [])  # specifically excluded fields
        for f in all_model_fields:
            # skip any fields not specified in data source
            if f.name not in fields or f.name in exclude:
                LOGGER.debug('skipping %s', f.name)
                continue
            # add field to parameters or update parameters with field type
            param_dict = {'ftype': f.get_internal_type()}
            if f.name in parameters:
                parameters[f.name]['extras'].update(param_dict)
            else:
                parameters[f.name] = DataParameter(**param_dict)
        super(DjangoModelReader, self).__init__(parameters, meta)

    def load_data(self, model_instance, *args, **kwargs):
        """
        Apply units to model.
        :return: data
        """
        model_dict = copy_model_instance(model_instance)
        return super(DjangoModelReader, self).load_data(**model_dict)


class HDF5Reader(ArgumentReader):
    """
    Reads data from an HDF5 file
    """
    #: True if reader accepts ``filename`` argument
    is_file_reader = True  # is a file reader

    def load_data(self, h5file, *args, **kwargs):
        with h5py.File(h5file) as h5f:
            h5data = dict.fromkeys(self.parameters)
            for param, attrs in self.parameters.iteritems():
                LOGGER.debug('parameter:\n%r', param)
                node = attrs['extras']['node']  # full name of node
                # composite datatype member
                member = attrs['extras'].get('member')
                if member is not None:
                    # if node is a table then get column/field/description
                    h5data[param] = np.asarray(h5f[node][member])  # copy member
                else:
                    h5data[param] = np.asarray(h5f[node])  # copy array
        return super(HDF5Reader, self).load_data(**h5data)
