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

from circus.core import UREG, Registry, CircusJSONEncoder, CommonBase
from data_readers import JSON_Reader
from circus.core.circus_exceptions import UncertaintyPercentUnitsError
import json
import os
import time
import functools
from copy import copy

DFLT_UNC = 1.0 * UREG['percent']  # default uncertainty


class DataRegistry(Registry):
    """
    A class for data sources and uncertainties
    """
    def __init__(self):
        #: meta names
        self._meta_names = ['uncertainty', 'isconstant', 'timeseries',
                            'data_source']
        # FIXME: check meta names so they don't override dict methods and
        # attributes
        super(DataRegistry, self).__init__()
        #: uncertainty
        self.uncertainty = {}
        #: ``True`` for each data-key if constant, ``False`` if periodic
        self.isconstant = {}
        #: name of corresponding time-series data, ``None`` if not time-series
        self.timeseries = {}
        #: name of :class:`DataSource`
        self.data_source = {}
        # FIXME: This is **brittle**, if meta_name added, but not added as
        # attribute then what? Also this is unnecessary double duty.
        # * Why not make instance attributes, class attributes?
        # * Use meta class? Have class factory add meta names as attr and list
        # them in meta_names?
        # * Just use meta_names, and use have Registry superclass add them?
        # * use vars(obj), dir(obj) or inspect.getmembers(obj, predicate)
        # __dict__() is same as vars(obj), dir(obj) is list of all attr names
        # incl bases, but vars(obj) is dictionary of only obj (or instance)
        # getmembers(obj, predicate) is same as dir(obj) but tuple, and
        # filtered when predicate true.

    def register(self, newdata, *args):
        """
        Register data in registry. Meta for each data is specified by positional
        arguments after the new data and consists of the following:

        * ``uncertainty`` - Map of corresponding uncertainties for new keys.
          The uncertainty keys must be a subset of the new data keys.
        * ``isconstant``: Map corresponding to new keys whose values are``True``
          if constant or ``False`` if periodic. These keys must be a subset of
          the new data keys.
        * ``timeseries``: Name of corresponding time series data, ``None`` if no
          time series. _EG_: DNI data ``timeseries`` attribute might be set to a
          date/time data that it corresponds to. More than one data can have the
          same ``timeseries`` data.
        * ``data_source``: the :class:`~circus.core.data_sources.DataSource`
          superclass that was used to acquire this data. This can be used to
          group data from a specific source together.

        :param newdata: New data to add to registry. When registering new data,
            keys are not allowed to override existing keys in the data
            registry.
        :type newdata: mapping
        :param args: uncertainty <float>, isconstant <bool>, timeseries
            <DataSource>, data_source <DataSource>
        :raises:
            :exc:`~circus.core.circus_exceptions.UncertaintyPercentUnitsError`
        """
        uncertainty, isconstant, timeseries, data_source = args
        # check uncertainty has units of percent
        if uncertainty:
            for k, v in uncertainty.iteritems():
                if v.units != UREG['percent']:
                    raise UncertaintyPercentUnitsError(k, v)
        # check that isconstant is boolean
        if isconstant:
            for k, v in isconstant.iteritems():
                if not isinstance(v, bool):
                    classname = self.__class__.__name__
                    error_msg = ['%s meta "isconstant" should be' % classname,
                                 'boolean, but it was "%s" for "%s".' % (v, k)]
                    raise TypeError(' '.join(error_msg))
        # call super method, meta must be passed as kwargs!
        super(DataRegistry, self).register(newdata, uncertainty=uncertainty,
                                           isconstant=isconstant,
                                           timeseries=timeseries,
                                           data_source=data_source)


class DataSourceBase(CommonBase):
    """
    Most general data source.
    """
    _path_attr = 'data_path'
    _file_attr = 'data_file'

    def __new__(mcs, name, bases, attr):
        # use only with Calc subclasses
        if not CommonBase.get_parents(bases, DataSourceBase):
            return super(DataSourceBase, mcs).__new__(mcs, name, bases, attr)
        # set param file full path if calculation path and file specified or
        # try to set parameters from class attributes except private/magic
        attr = mcs.set_param_file_or_parameters(attr)
        return super(DataSourceBase, mcs).__new__(mcs, name, bases, attr)


class DataSource(object):
    """
    Required interface for all Circus data sources such as PVSim results,
    TMY3 data and calculation input files.

    Each data source must specify a ``data_reader`` which must subclass
    :class:`~circus.core.data_readers.DataReader` and that can read this data
    source. The default is :class:`~circus.core.data_readers.JSON_Reader`.

    Each data source must also specify a ``data_file`` and ``data_path`` that
    contains the parameters required to import data from the data source using
    the data reader. Each data reader had different parameters to specify how
    it reads the data source, so consult the API.

    This is the required interface for all source files containing data used in
    Circus.
    """
    __metaclass__ = DataSourceBase
    #: data reader, default is :class:`~circus.core.data_readers.JSON_Reader`
    data_reader = JSON_Reader  # can be overloaded in superclass

    def __init__(self, filename):
        #: filename of file containing data
        self.filename = filename
        # check superclass for param_file created by metaclass otherwise use
        # class attributes directly as parameters created in CommonBase
        if hasattr(self, 'param_file'):
            # read and load JSON parameter map file as "parameters"
            with open(self.param_file, 'r') as fp:
                #: dictionary of parameters for reading data source file
                self.parameters = json.load(fp)
        else:
            #: parameter file
            self.param_file = None
        # private property
        self._is_saved = True
        # If filename ends with ".json"
        # * JSON_Reader is original reader or data entered via UI.
        # * Different original reader, data edited, saved as JSON.
        # If file does **not** end with ".json", save data in file with ".json"
        # appended to original filename, pass original data reader as extra arg
        if self._is_cached():
            # switch reader to JSON_Reader, with old reader as extra arg
            proxy_data_reader = functools.partial(
                JSON_Reader, data_reader=self.data_reader
            )
        else:
            proxy_data_reader = self.data_reader
        # create the data reader object specified using parameter map
        data_reader_instance = proxy_data_reader(self.filename, self.parameters)
        #: data loaded from reader
        self.data = data_reader_instance.load_data()
        # save JSON file if doesn't exist already. JSON_Reader checks utc mod
        # time vs orig file, and deletes JSON file if orig file is newer.
        if not self._is_cached():
            self.saveas_json(self.filename)  # ".json" appended by saveas_json
        # XXX: default values of uncertainty, isconstant and timeseries are
        # empty dictionaries.
        #: data uncertainty in percent
        self.uncertainty = {}
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

    def _is_cached(self, ex='.json'):
        """
        Determine if ``filename`` is cached using extension ``ex`` a string.

        :param ex: extension used to cache ``filename``, default is '.json'
        :type ex: str
        :return: True if ``filename`` is cached using extensions ``ex``
        :rtype: bool
        """
        return self.filename.endswith(ex) or os.path.exists(self.filename + ex)

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
        # JSONEncoder removes units and converts arrays to lists
        # save last time file was modified
        utc_mod_time = list(time.gmtime(os.path.getmtime(save_name)))
        json_data = {'data': self.data, 'utc_mod_time': utc_mod_time,
                     'param_file': self.param_file,
                     'data_reader': self.data_reader.__name__,
                     'data_source': self.__class__.__name__}
        if not save_name.endswith('.json'):
            save_name += '.json'
        with open(save_name, 'w') as fp:
            json.dump(json_data, fp, cls=CircusJSONEncoder)
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
