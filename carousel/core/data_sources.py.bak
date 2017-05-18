# -*- coding: utf-8 -*-
"""
This module provides base classes for data sources. Data sources provide
data to calculations. All data used comes from a data source. The requirements
for data sources are as follows:

1. Data sources must be sub-classed to :class:`DataSource`.
2. They must know where to get their data, either from a file or from other
    data sources.
3. They need a data reader that knows how to extract the data from the file,
    or combine data in calculations to produce new data.
4. They require a parameter map that states exactly where the data is and what
    its units are, what the data will be called in calculations and any other
    meta-data the registry requires.
"""

from carousel.core import (
    UREG, Registry, CarouselJSONEncoder, CommonBase, Parameter
)
from carousel.core.data_readers import JSONReader
from carousel.core.exceptions import (
    UncertaintyPercentUnitsError, UncertaintyVarianceError
)
import json
import os
import time
from copy import copy
import numpy as np

DFLT_UNC = 1.0 * UREG('percent')  # default uncertainty


class DataParameter(Parameter):
    """
    Field for data parameters.
    """
    _attrs = ['units', 'uncertainty', 'isconstant', 'timeseries']


class DataRegistry(Registry):
    """
    A registry for data sources. The meta names are: ``uncertainty``,
    ``variance``, ``isconstant``, ``timeseries`` and ``data_source``
    """
    #: meta names
    meta_names = ['uncertainty', 'variance', 'isconstant', 'timeseries',
                  'data_source']

    def register(self, newdata, *args, **kwargs):
        """
        Register data in registry. Meta for each data is specified by positional
        or keyword arguments after the new data and consists of the following:

        * ``uncertainty`` - Map of uncertainties in percent corresponding to new
          keys. The uncertainty keys must be a subset of the new data keys.
        * ``variance`` - Square of the uncertainty (no units).
        * ``isconstant``: Map corresponding to new keys whose values are``True``
          if constant or ``False`` if periodic. These keys must be a subset of
          the new data keys.
        * ``timeseries``: Name of corresponding time series data, ``None`` if no
          time series. _EG_: DNI data ``timeseries`` attribute might be set to a
          date/time data that it corresponds to. More than one data can have the
          same ``timeseries`` data.
        * ``data_source``: the
          :class:`~carousel.core.data_sources.DataSource` superclass that
          was used to acquire this data. This can be used to group data from a
          specific source together.

        :param newdata: New data to add to registry. When registering new data,
            keys are not allowed to override existing keys in the data
            registry.
        :type newdata: mapping
        :raises:
            :exc:`~carousel.core.exceptions.UncertaintyPercentUnitsError`
        """
        kwargs.update(zip(self.meta_names, args))
        # check uncertainty has units of percent
        uncertainty = kwargs['uncertainty']
        variance = kwargs['variance']
        isconstant = kwargs['isconstant']
        # check uncertainty is percent
        if uncertainty:
            for k0, d in uncertainty.iteritems():
                for k1, v01 in d.iteritems():
                    units = v01.units
                    if units != UREG('percent'):
                        keys = '%s-%s' % (k0, k1)
                        raise UncertaintyPercentUnitsError(keys, units)
        # check variance is square of uncertainty
        if variance and uncertainty:
            for k0, d in variance.iteritems():
                for k1, v01 in d.iteritems():
                    keys = '%s-%s' % (k0, k1)
                    missing = k1 not in uncertainty[k0]
                    v2 = np.asarray(uncertainty[k0][k1].to('fraction').m) ** 2.0
                    if missing or not np.allclose(np.asarray(v01), v2):
                        raise UncertaintyVarianceError(keys, v01)
        # check that isconstant is boolean
        if isconstant:
            for k, v in isconstant.iteritems():
                if not isinstance(v, bool):
                    classname = self.__class__.__name__
                    error_msg = ['%s meta "isconstant" should be' % classname,
                                 'boolean, but it was "%s" for "%s".' % (v, k)]
                    raise TypeError(' '.join(error_msg))
        # call super method, meta must be passed as kwargs!
        super(DataRegistry, self).register(newdata, **kwargs)


class DataSourceBase(CommonBase):
    """
    Base data source meta class.
    """
    _path_attr = 'data_path'
    _file_attr = 'data_file'
    _param_cls = DataParameter
    _reader_attr = 'data_reader'
    _enable_cache_attr = 'data_cache_enabled'
    _attr_default = {_reader_attr: JSONReader, _enable_cache_attr: True}

    def __new__(mcs, name, bases, attr):
        # use only with DataSource subclasses
        if not CommonBase.get_parents(bases, DataSourceBase):
            return super(DataSourceBase, mcs).__new__(mcs, name, bases, attr)
        # set _meta combined from bases
        attr = mcs.set_meta(bases, attr)
        # set default meta attributes
        meta = attr[mcs._meta_attr]
        for ma, dflt in mcs._attr_default.iteritems():
            a = getattr(meta, ma, None)
            if a is None:
                setattr(meta, ma, dflt)
        # set param file full path if data source path and file specified or
        # try to set parameters from class attributes except private/magic
        attr = mcs.set_param_file_or_parameters(attr)
        return super(DataSourceBase, mcs).__new__(mcs, name, bases, attr)


class DataSource(object):
    """
    Required interface for all Carousel data sources such as PVSim results,
    TMY3 data and calculation input files.

    Each data source must specify a ``data_reader`` which must subclass
    :class:`~carousel.core.data_readers.DataReader` and that can read this
    data source. The default is
    :class:`~carousel.core.data_readers.JSONReader`.

    Each data source must also specify a ``data_file`` and ``data_path`` that
    contains the parameters required to import data from the data source using
    the data reader. Each data reader had different parameters to specify how
    it reads the data source, so consult the API.

    This is the required interface for all source files containing data used in
    Carousel.
    """
    __metaclass__ = DataSourceBase

    def __init__(self, *args, **kwargs):
        # save arguments, might need them later
        self.args = args  #: positional arguments
        self.kwargs = kwargs  #: keyword arguments
        # make pycharm by defining inferred objects
        meta = getattr(self, DataSourceBase._meta_attr)
        parameters = getattr(self, DataSourceBase._param_attr)
        # check if the data reader is a file reader
        filename = None
        if meta.data_reader.is_file_reader:
            # get filename from args or kwargs
            if args:
                filename = args[0]
            elif kwargs:
                filename = kwargs.get('filename')
                # raises KeyError: 'filename' if filename isn't given
        # TODO: allow user to set explicit filename for cache
        #: filename of file containing data
        self.filename = filename
        # private property
        self._is_saved = True
        # If filename ends with ".json", then either the original reader was
        # a JSONReader or the data was cached.
        # If data caching enabled and file doesn't end with ".json", cache it as
        # JSON, append ".json" to the original filename and pass original data
        # reader as extra argument.
        if meta.data_cache_enabled and self._is_cached():
            # switch reader to JSONReader, with old reader as extra arg
            data_reader_instance = JSONReader(parameters, meta)
        else:
            # create the data reader object specified using parameter map
            data_reader_instance = meta.data_reader(parameters, meta)
        #: data loaded from reader
        self.data = data_reader_instance.load_data(*args, **kwargs)
        # save JSON file if doesn't exist already. JSONReader checks utc mod
        # time vs orig file, and deletes JSON file if orig file is newer.
        if meta.data_cache_enabled and not self._is_cached():
            self.saveas_json(self.filename)  # ".json" appended by saveas_json
        # XXX: default values of uncertainty, isconstant and timeseries are
        # empty dictionaries.
        #: data uncertainty in percent
        self.uncertainty = {}
        #: variance
        self.variance = {}
        #: ``True`` if data is constant for all dynamic calculations
        self.isconstant = {}
        #: name of corresponding time series data, ``None`` if no time series
        self.timeseries = {}
        #: name of :class:`DataSource`
        self.data_source = dict.fromkeys(self.data, self.__class__.__name__)
        # TODO: need a consistent way to handle uncertainty, isconstant and time
        # series
        # XXX: Each superclass should do the following:
        # * prepare the raw data from reader for the registry. Some examples of
        #   data preparation are combining numbers and units and uncertainties,
        #   data validation, combining years, months, days and hours into
        #   datetime objects and parsing data from strings.
        # * handle uncertainty, isconstant, timeseries and any other meta data.
        self._raw_data = copy(self.data)  # shallow copy of data
        self.__prepare_data__()  # prepare data for registry
        # calculate variances
        for k0, d in self.uncertainty.iteritems():
            for k1, v01 in d.iteritems():
                self.variance[k0] = {k1: v01.to('fraction').m ** 2.0}

    def __prepare_data__(self):
        """
        Prepare raw data from reader for the registry. Some examples of data
        preparation are combining numbers and units and uncertainties, data
        validation, combining years, months, days and hours into datetime
        objects and parsing data from strings.

        Each data superclass should implement this method. If there is no data
        preparation then use ``pass``.
        """
        raise NotImplementedError('Data preparation not implemented. ' +
                                  'Use ``pass`` if not required.')

    def _is_cached(self, ext='.json'):
        """
        Determine if ``filename`` is cached using extension ``ex`` a string.

        :param ext: extension used to cache ``filename``, default is '.json'
        :type ext: str
        :return: True if ``filename`` is cached using extensions ``ex``
        :rtype: bool
        """
        # extension must start with a dot
        if not ext.startswith('.'):
            # prepend extension with a dot
            ext = '.%s' % ext
        # cache file is filename with extension
        cache_file = '%s%s' % (self.filename, ext)
        # if filename already ends with extension or there's a file with the
        # extension, then assume the data is cached
        return self.filename.endswith(ext) or os.path.exists(cache_file)

    @property
    def issaved(self):
        return self._is_saved

    def saveas_json(self, save_name):
        """
        Save :attr:`data`, :attr:`param_file`, original :attr:`data_reader`
        and UTC modification time as keys in JSON file. If data is edited then
        it should be saved using this method. Non-JSON data files are also
        saved using this method.

        :param save_name: Name to save JSON file as, ".json" is appended.
        :type save_name: str
        """
        # make pycharm by defining inferred objects
        meta = getattr(self, DataSourceBase._meta_attr)
        param_file = getattr(self, DataSourceBase._param_file)
        # JSONEncoder removes units and converts arrays to lists
        # save last time file was modified
        utc_mod_time = list(time.gmtime(os.path.getmtime(save_name)))
        json_data = {'data': self.data, 'utc_mod_time': utc_mod_time,
                     'param_file': param_file,
                     'data_reader': meta.data_reader.__name__,
                     'data_source': self.__class__.__name__}
        if not save_name.endswith('.json'):
            save_name += '.json'
        with open(save_name, 'w') as fp:
            json.dump(json_data, fp, cls=CarouselJSONEncoder)
        # TODO: test file save successful
        # TODO: need to update model
        self._is_saved = True

    def edit(self, edits, data_reg):
        """
        Edit data in :class:`Data_Source`. Sets :attr:`issaved` to ``False``.
        """
        data_reg.update(edits)
        self._is_saved = False

    def __getitem__(self, item):
        return self.data[item]

    def __repr__(self):
        parameters = getattr(self, DataSourceBase._param_attr)
        fmt = ('<%s(' % self.__class__.__name__)
        fmt += ', '.join('%s=%r' % (k, v) for k, v in parameters.iteritems())
        fmt += ')>'
        return fmt
