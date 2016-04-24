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

from circus.core import UREG, YEAR, _DATA, Registry, CircusJSONEncoder
from data_readers import XLRD_Reader, NumPyLoadTxtReader, \
    NumPyGenFromTxtReader, Parameterized_XLS, JSON_Reader, Mixed_Text_XLS
from circus.core.circus_exceptions import PVSimTimezoneError, \
    UncertaintyPercentUnitsError, UncertaintyBoundsUnitsError
import json
import numpy as np
from datetime import datetime, timedelta
import os
import re
import time
import importlib
from xlrd import xldate_as_tuple, open_workbook

DFLT_UNC = 1 * UREG['%']  # default uncertainty


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

    def register(self, newdata, uncertainty, isconstant, timeseries,
                 data_source):
        """
        Register data in registry.

        :param newdata: New data to add to registry. When registering new data,
            keys are not allowed to override existing keys in the data
            registry.
        :type newdata: mapping
        :param uncertainty: Map of corresponding uncertainties for new keys.
            The uncertainty keys must be a subset of the new data keys.
        :type uncertainty: mapping
        :param isconstant: Map corresponding to new keys whose values are
            ``True`` if constant or ``False`` if periodic. These keys must be a
            subset of the new data keys.
        :type isconstant: mapping
        :param timeseries: Name of corresponding time-series data, ``None`` if
            not time-series
        :type timeseries: dict
        :param data_source: Name of the :class:`DataSource`.
        :type data_source: dict
        :raises: :exc:`~circus.core.circus_exceptions.UncertaintyPercentUnitsError`
        """
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


class DataSource(object):
    """
    Required interface for all Circus data sources such as PVSim results,
    TMY3 data and calculation input files.

    :param filename: Filename of the data source.
    :type filename: str
    :param data_reader: A reader for this data source.
    :type data_reader: \
        :class:`~circus.core.data_readers.DataReader`
    :param param_file: A JSON file that contains the a parameter map for the
        data reader.
    :type param_file: str
    """
    def __init__(self, filename, data_reader, param_file):
        #: filename of file containing data
        self.filename = filename
        #: parameter file
        self.param_file = param_file
        #: data reader
        self.data_reader = data_reader
        # private property
        self._is_saved = True
        # read and load JSON parameter map file as "parameters"
        with open(param_file, 'r') as fp:
            #: dictionary of parameters for reading data source file
            self.parameters = json.load(fp)
        # JSON_Reader is the default reader
        # If filename ends with ".json"
        # * JSON_Reader is original reader or data entered via UI.
        # * Different original reader, data edited, saved as JSON.
        # If file does **not** end with ".json", save data in file with ".json"
        # appended to original filename, pass original data reader as extra arg
        if (self.filename.endswith('.json') or
            os.path.exists(self.filename + '.json')):
            # switch reader to JSON_Reader, with old reader as extra arg
            data_reader = lambda filename, param: JSON_Reader(filename, param,
                                                              self.data_reader)
        # create the data reader object specified using parameter map
        _data_reader = data_reader(self.filename, self.parameters)
        #: data loaded from reader
        self.data = _data_reader.load_data()
        # save JSON file if doesn't exist already. JSON_Reader checks utc mod
        # time vs orig file, and deletes JSON file if orig file is newer.
        if not (self.filename.endswith('.json') or
                os.path.exists(self.filename + '.json')):
            self.saveas_JSON(self.filename)  # ".json" appended by saveas_JSON
        # NOTE: each subclass must set uncertainty and isconstant attributes,
        # or AttributeError is raised!
        # TODO: put uncertainty here! it is copied exactly the same in every
        # data source

    @property
    def issaved(self):
        return self._is_saved

    def saveas_JSON(self, save_name):
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


class MetaUserDataSource(type):
    """
    Most general data source.
    """
    def __new__(cls, name, bases, attr):
        # filter out bases from which DataSource is derived
        bases = tuple([b for b in bases if not b in DataSource.__bases__])
        if DataSource not in bases:
            bases += (DataSource,)  # add DataSource to bases
        param_file = os.path.join(attr['data_path'], attr['data_file'])

        def __init__(self, filename):
            DataSource.__init__(self, filename, attr['data_reader'],
                                param_file)
            #: solder joint failure uncertainty in percent
            self.uncertainty = {}
            #: all solder joint failure parameters are constant
            self.isconstant = dict.fromkeys(self.data, True)
            #: name of corresponding time-series data, ``None`` if not
            self.timeseries = {}
            #: name of :class:`DataSource`
            self.data_source = dict.fromkeys(self.data,
                                             self.__class__.__name__)
            # TODO: refactor "isconstant" same for ever class
            # TODO: refactor "uncertainty" to remove redundancy, several data
            # sources use exactly the same code.
            for sheet_params in self.parameters.itervalues():
                for k, v in sheet_params.iteritems():
                    try:
                        unc_param = v['uncertainty']  # uncertainty parameters
                    except KeyError:
                        # skip keys without uncertainty
                        continue  # do not raise exception if no unc key
                    else:
                        # uncertainty is null, use default
                        if not unc_param:
                            self.uncertainty[k] = DFLT_UNC
                        elif isinstance(unc_param, basestring):
                            # uncertainty mapped to another data field
                            self.uncertainty[k] = self.data[unc_param]
                            self.data.pop(unc_param)  # pop uncertainty
                            self.isconstant.pop(unc_param)  # added in constructor
                            self.data_source.pop(unc_param)  # added in constructor
                        else:
                            self.uncertainty[k] = unc_param

        attr['__init__'] = __init__
        return super(MetaUserDataSource, cls).__new__(cls, name, bases, attr)

    def __init__(self, name, bases, attr):
        super(MetaUserDataSource, self).__init__(name, bases, attr)


class MetaDataSource(MetaUserDataSource):
    """
    Data source that uses :data:`_DATA` data path. Only valid for
    :class:`~data_readers.XLRD_Reader`.
    """
    def __new__(cls, name, bases, attr):
        attr['data_reader'] = XLRD_Reader
        attr['data_path'] = _DATA
        return super(MetaDataSource, cls).__new__(cls, name, bases, attr)

# TODO: move attr/meth to base class, refactor to eliminate redundant code and
# simplify API
