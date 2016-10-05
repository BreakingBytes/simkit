# -*- coding: utf-8 -*-
"""
This module provides the base classes for data readers, such as
`XLRD <https://pypi.python.org/pypi/xlrd/0.9.2>`_ and :func:`numpy.loadtxt`,
which are used to read in data sources.
"""

from StringIO import StringIO
from carousel.core import UREG, Q_
from carousel.core.exceptions import (
    UnnamedDataError, MixedTextNoMatchError
)
from xlrd import open_workbook
import csv
import numpy as np
import json
import os
import time
import re

# regex pattern for %e, %E, %f and %g
# http://docs.python.org/2/library/re.html#simulating-scanf
# use (?...) for non capturing groups
EFG_PATTERN = '([-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][-+]?\\d+)?)'
# whitelist regex methods
RE_METH = ['search', 'match', 'findall', 'split']


class DataReader(object):
    """
    Required interface for all Carousel data readers.

    :param parameters: parameters to be read
    :type parameters: dict
    """
    #: True if reader accepts ``filename`` argument
    is_file_reader = True  # overload in subclasses

    def __init__(self, parameters):
        #: parameters to be read by reader
        self.parameters = parameters

    def load_data(self, *args, **kwargs):
        """
        Load data from source  using reader. This method must be implemented by
        each data reader.

        :param args: positional arguments
        :param kwargs: keyword arguments
        :returns: data read by :class:`DataReader`
        :rtype: dict
        :raises: :exc:`~exceptions.NotImplementedError`
        """
        raise NotImplementedError('load_data')

    def apply_units_to_cache(self, data):
        """
        Apply units to cached data. This method must be implemented by each data
        reader.

        :param data: cached data
        :return: data with units applied
        :rtype: :class:`~pint.unit.Quantity`
        :raises: :exc:`~exceptions.NotImplementedError`
        """
        raise NotImplementedError('apply_units_to_cache')


class JSONReader(DataReader):
    """
    Read data from a JSON file.

    :param parameters: parameters to read
    :type parameters: dict
    :param data_reader: original :class:`DataReader` if data cached as JSON

    This the default data reader if not specified in the data source. The format
    of the data is similar to the dictionary used to create the data registry,
    except without units.

    For example::

        {
            "data": {
                "DNI": [834, 523, 334, 34, 0, 0],
                "zenith": [21, 28, 45, 79, 90, 90]
            },
            "param_file": "path/to/corresponding/param_file.json",
            "data_source": "MyDataSource"
        }

    Parameters can be specified in a JSON file. ::

        {
            "DNI": {
                "description": "direct normal insolation",
                "units": "W/m*^2",
                "isconstant": false
            },
            "zenith": {
                "description": "solar zenith",
                "units": "degrees",
                "isconstant": false
            }
        }

    Parameters can also be specified in the data source as class attributes. ::

        class MyDataSrc(DataSource):
            data_reader = JSONReader
            DNI = {
                "description": "direct normal insolation",
                "units": "W/m*^2",
                "isconstant": false
            }
            zenith = {
                "description": "solar zenith",
                "units": "degrees",
                "isconstant": false
            }

    """
    def __init__(self, parameters, data_reader=None):
        super(JSONReader, self).__init__(parameters)
        #: origin data reader [None]
        self.orig_data_reader = data_reader

    def load_data(self, filename, *args, **kwargs):
        """
        Load JSON data.

        :param filename: name of JSON file with data
        :type filename: str
        :return: data
        :rtype: dict
        """
        # append .json extension if needed
        if not filename.endswith('.json'):
            filename += '.json'  # append "json" to filename
        # open file and load JSON data
        with open(filename, 'r') as fid:
            json_data = json.load(fid)
        # if JSONReader is the original reader then apply units and return
        if (not self.orig_data_reader or
                isinstance(self, self.orig_data_reader)):
            return self.apply_units_to_cache(json_data['data'])
        # last modification since JSON file was saved
        utc_mod_time = json_data.get('utc_mod_time')
        # instance of original data reader with original parameters
        orig_data_reader_obj = self.orig_data_reader(self.parameters)
        # check if file has been modified since saved as JSON file
        if utc_mod_time:
            # convert to ordered tuple
            utc_mod_time = time.struct_time(utc_mod_time)
            orig_filename = filename[:-5]  # original filename
            # use original file if it's been modified since JSON file saved
            if utc_mod_time < time.gmtime(os.path.getmtime(orig_filename)):
                os.remove(filename)  # delete JSON file
                return orig_data_reader_obj.load_data(orig_filename)
        # use JSON file if original file hasn't been modified
        return orig_data_reader_obj.apply_units_to_cache(json_data['data'])

    def apply_units_to_cache(self, data):
        """
        Apply units to data read using :class:`JSONReader`.

        :param data: cached data
        :return: data with units applied
        :rtype: :class:`~pint.unit.Quantity`
        """
        for k, val in self.parameters.iteritems():
            if 'units' in val:
                data[k] = Q_(data[k], val.get('units'))
        return data


class XLRDReader(DataReader):
    """
    Read data using XLRD.

    The :attr:`~DataReader.parameters` argument must be a dictionary. Each
    sheet in the file to read should be a key in
    :attr:`~DataReader.parameters`. The value of each sheet-key is also a
    dictionary. The names of parameters to read are the keys in the sheet-key
    dictionary. Finally each name-key is a dictionary that contains the
    following keys: "description", "units" and "range".

    If the range is a ...

    * single cell -- use [rowx, colx].
    * 2-D range -- use 2 arrays, [start, stop], each with [rowx, colx].
    * column slice -- use an array and an int, [slice, colx], in which slice is
      [start-rowx, stop-rowx]. Set stop-rowx to ``None`` to read the rest of
      the column after start-rowx.
    * row slice -- use [rowx, slice] in which slice is [start-colx, stop-colx].
      Set stop-colx to ``None`` to read the rest of the row after start-colx.
    * column -- use [None, colx] or [[], colx]
    * row -- use [rowx, None] or [rowx, []]

    .. seealso::
        `The xlrd Module <https://secure.simplistix.co.uk/svn/xlrd/tags/ \
            0.7.3/xlrd/doc/xlrd.html>`_

    Example of :attr:`~DataReader.parameters`::

        parameters = {
            'Level 1 Outputs': {
                'month': {
                    'description': 'month of year',
                    'units': 'month',
                    'range': [[2, 8762], 2]},
                'day': {
                    'description': 'day of month',
                    'units': 'day',
                    'range': [[2, 8762], 3]}},
            'Level 2 Outputs': {
                'PAC': {
                    'description': 'AC power',
                    'units': 'kW',
                    'range': [[2, 8762], 12]},
                'PDC': {
                    'description': 'DC power',
                    'units': 'kW',
                    'range': [[2, 8762], 13]}}}

    This loads "month" and "day" data from columns 2 and 3 in the "Level 1
    Outputs" sheet and "PAC" and "PDC" data from columns 12 and 13 in the
    "Level 2 Outputs" sheets. The units for each data set and a description is
    also given. Each of the data columns is 8760 rows long, from row 2 to row
    8762. Don't forget that indexing starts at 0, so row 2 is the 3rd row.
    """

    def load_data(self, filename, *args, **kwargs):
        """
        Load parameters from Excel spreadsheet.

        :param filename: Name of Excel workbook with data.
        :type filename: str
        :returns: Data read from Excel workbook.
        :rtype: dict
        """
        # workbook read from file
        workbook = open_workbook(filename, verbosity=True)
        data = {}  # an empty dictionary to store data
        # iterate through sheets in parameters
        for sheet, sheet_params in self.parameters.iteritems():
            # get each worksheet from the workbook
            worksheet = workbook.sheet_by_name(sheet)
            # iterate through the parameters on each sheet
            for param, pval in sheet_params.iteritems():
                # split the parameter's range elements
                prng0, prng1 = pval['range']
                # missing "units", json ``null`` and Python ``None`` all OK!
                # convert to str from unicode, None to '' (dimensionless)
                punits = str(pval.get('units') or '')
                # replace None with empty list
                if prng0 is None:
                    prng0 = []
                if prng1 is None:
                    prng1 = []
                # FIXME: Use duck-typing here instead of type-checking!
                # if both elements in range are `int` then parameter is a cell
                if isinstance(prng0, int) and isinstance(prng1, int):
                    datum = worksheet.cell_value(prng0, prng1)
                # if the either element is a `list` then parameter is a slice
                elif isinstance(prng0, list) and isinstance(prng1, int):
                    datum = worksheet.col_values(prng1, *prng0)
                elif isinstance(prng0, int) and isinstance(prng1, list):
                    datum = worksheet.row_values(prng0, *prng1)
                # if both elements are `list` then parameter is 2-D
                else:
                    datum = []
                    for col in xrange(prng0[1], prng1[1]):
                        datum.append(worksheet.col_values(col, prng0[0],
                                                          prng1[0]))
                # duck typing that datum is real
                try:
                    npdatum = np.array(datum, dtype=np.float)
                except ValueError as err:
                    # check for iterable:
                    # if `datum` can't be coerced to float, then it must be
                    # *string* & strings *are* iterables, so don't check!
                    # check for strings:
                    # data must be real or *all* strings!
                    # empty string, None or JSON null also OK
                    # all([]) == True but any([]) == False
                    if not datum:
                        data[param] = None  # convert empty to None
                    elif all(isinstance(_, basestring) for _ in datum):
                        data[param] = datum  # all str is OK (EG all 'TMY')
                    elif all(not _ for _ in datum):
                        data[param] = None  # convert list of empty to None
                    else:
                        raise err  # raise ValueError if not all real or str
                else:
                    data[param] = npdatum * UREG[punits]
                # FYI: only put one statement into try-except test otherwise
                # might catch different error than expected. use ``else`` as
                # option to execute only if exception *not* raised.
        return data

    def apply_units_to_cache(self, data):
        """
        Apply units to cached data read using :class:`JSONReader`.

        :param data: Cached data.
        :type data: dict
        :return: data with units
        """
        # iterate through sheets in parameters
        for sheet_params in self.parameters.itervalues():
            # iterate through the parameters on each sheet
            for param, pval in sheet_params.iteritems():
                # try to apply units
                try:
                    data[param] *= UREG[str(pval.get('units') or '')]
                except TypeError:
                    continue
        return data


class NumPyLoadTxtReader(DataReader):
    """
    Read data using :func:`numpy.loadtxt` function.

    The :attr:`~DataReader.parameters` argument is a dictionary that must have
    a "data" key. An additional "header" is optional; see :func:`_read_header`.

    The "data" key provides arguments to :func:`numpy.loadtxt`. The "dtype" key
    must be specified, as names are required for all data in Carousel. Some
    of the other :func:`numpy.loadtxt` arguments: "delimiter" and "skiprows" can
    also be specified as keys. In addition "units" can also be specified in a
    dictionary in which the keys are the names of the data output by
    :func:`numpy.loadtxt`.  Converters are not permitted. The "usecols"
    argument is also not used since :func:`numpy.loadtxt` states that "the
    number of columns used must match the number of fields in the data-type"
    and "dtype" is already specified. The other arguments, "fname", "comments",
    "unpack" and "ndmin" are also not used.

    Example of :attr:`~DataReader.parameters`::

        parameters = {
            'header': {
                'delimiter': ',',
                'fields': [
                    ['Name', 'str'],
                    ['Latitude', 'float', 'arcdegree'],
                    ['Longitude', 'float', 'arcdegree']]},
            'data': {
                'dtype': [
                    ['Date', '(3,)int'], ['Time', '(2,)int'],
                    ['GHI', 'float'], ['DNI', 'float'], ['DHI', 'float']],
                'units': {
                    'GHI': 'W/m**2', 'DNI': 'W/m**2', 'DHI': 'W/m**2'},
                'usecols': [0, 1, 4, 7, 10]}}

    This loads a header with 3 fields followed by 5 columns of data, converting
    the 1st column, "Date", to a 3-element tuple of ``int`` and the 2nd column,
    "Time", to a 2-element tuple of ``int``.
    """

    def load_data(self, filename, *args, **kwargs):
        """
        load data from text file.

        :param filename: name of text file to read
        :type filename: str
        :returns: data read from file using :func:`numpy.loadtxt`
        :rtype: dict
        """
        # header keys
        header_param = self.parameters.get('header')  # default is None
        # data keys
        data_param = self.parameters['data']  # raises KeyError if no 'data'
        dtype = data_param['dtype']  # raises KeyError if no 'dtype'
        # convert to tuple and normal ASCII
        _utf8_list_to_ascii_tuple(dtype) if dtype else None  # -> tuple of str
        delimiter = data_param.get('delimiter')  # default is None
        skiprows = data_param.get('skiprows')  # default is None
        data_units = data_param.get('units', {})  # default is an empty dict
        data = {}  # a dictionary for data
        # open file for reading
        with open(filename, 'r') as fid:
            # read header
            if header_param:
                data.update(_read_header(fid, header_param))
                fid.seek(0)  # move cursor back to beginning
            # read data
            data_data = np.loadtxt(fid, dtype, delimiter=delimiter,
                                   skiprows=skiprows)
        # apply units
        data.update(_apply_units(data_data, data_units, fid.name))
        return data

    def apply_units_to_cache(self, data):
        """
        Apply units to data originally loaded by :class:`NumPyLoadTxtReader`.
        """
        return _apply_units_to_numpy_data_readers(self.parameters, data)


class NumPyGenFromTxtReader(DataReader):
    """
    Read data using :func:`numpy.genfromtxt` function.

    The :attr:`~DataReader.parameters` argument is a dictionary that must have
    a "data" key. An additional "header" is optional; see :func:`_read_header`.

    The "data" key provides arguments to :func:`numpy.genfromtxt`. Either the
    "dtype" or "names" key must be specified, as names are required for all
    data in Carousel. Some of the other :func:`numpy.genfromtxt` arguments:
    "delimiter", "skip_header", "usecols", "excludelist" and "deletechars" can
    also be specified as keys. In addition "units" can also be specified in a
    dictionary in which the keys are the names of the data output by
    :func:`numpy.genfromtxt`. Converters are not permitted. The other
    arguments, "fname", "comments", "skip_footer", "missing_values",
    "filling_values", "defaultfmt", "autostrip", "replace_space",
    "case_sensitive", "unpack", "usemask" and "invalid_raise" are also not
    used.

    If the data names are not specified in the "dtypes" key or "names" key,
    then :meth:`~NumPyGenFromTxtReader.load_data` will raise an exception,
    :exc:`~carousel.core.exceptions.UnnamedDataError`.

    .. seealso::
        `Importing data with genfromtxt \
            <http://docs.scipy.org/doc/numpy/user/basics.io.genfromtxt.html>`_

    Example of :attr:`~DataReader.parameters`::

        parameters = {
            'header': {
                'delimiter': ' ',
                'fields': [
                    ['city', 'str'], ['state', 'str'],
                    ["timezone", 'int'], ["elevation", 'int', 'meters']]},
            'data': {
                'delimiter': 4,
                'names': ['DNI', 'DHI', 'GHI'],
                'units': {'DNI': 'W/m**2', 'DHI': 'W/m**2', 'GHI': 'W/m**2'}}}

    This loads a header that is delimited by whitespace, followed by data in
    three fixed-width columns all 4-digit floats.
    """

    def load_data(self, filename, *args, **kwargs):
        """
        load data from text file.

        :param filename: name of file to read
        :type filename: str
        :returns: data read from file using :func:`numpy.genfromtxt`
        :rtype: dict
        :raises: :exc:`~carousel.core.exceptions.UnnamedDataError`
        """
        # header keys
        header_param = self.parameters.get('header')  # default is None
        # data keys
        data_param = self.parameters['data']  # raises KeyError if no 'data'
        dtype = data_param.get('dtype')  # default is None
        # if not None convert to tuple and normal ASCII
        _utf8_list_to_ascii_tuple(dtype) if dtype else None  # -> tuple of str
        delimiter = data_param.get('delimiter')  # default is None
        skip_header = data_param.get('skip_header')  # default is None
        usecols = data_param.get('usecols')  # default is None
        names = data_param.get('names')  # default is None
        names = [str(_) for _ in names] if names else None  # -> str
        excludelist = data_param.get('excludelist')  # default is None
        deletechars = data_param.get('deletechars')  # default is None
        data_units = data_param.get('units', {})  # default is an empty dict
        # either dtype or names must be specified
        if not (dtype or names):
            raise UnnamedDataError(filename)
        data = {}  # a dictionary for data
        # open file for reading
        with open(filename, 'r') as fid:
            # read header
            if header_param:
                data.update(_read_header(fid, header_param))
                fid.seek(0)  # move cursor back to beginning
            # data
            data_data = np.genfromtxt(fid, dtype, delimiter=delimiter,
                                      skip_header=skip_header, usecols=usecols,
                                      names=names, excludelist=excludelist,
                                      deletechars=deletechars)
        # apply units
        data.update(_apply_units(data_data, data_units, fid.name))
        return data

    def apply_units_to_cache(self, data):
        """
        Apply units to data originally loaded by :class:`NumPyLoadTxtReader`.
        """
        return _apply_units_to_numpy_data_readers(self.parameters, data)


def _apply_units_to_numpy_data_readers(parameters, data):
    """
    Apply units to data originally loaded by :class:`NumPyLoadTxtReader` or
    :class:`NumPyGenFromTxtReader`.

    :param parameters: Dictionary of data source parameters read from JSON
        file.
    :type parameters: dict
    :param data: Dictionary of data read
    """
    # apply header units
    header_param = parameters.get('header')  # default is None
    # check for headers
    if header_param:
        fields = header_param['fields']  # header fields
        # dictionary of header field parameters
        header_fields = {field[0]: field[1:] for field in fields}
        # loop over fieldnames
        for k, val in header_fields.iteritems():
            # check for units in header field parameters
            if len(val) > 1:
                data[k] *= UREG[str(val[1])]  # apply units
    # apply other data units
    data_units = parameters['data'].get('units')  # default is None
    if data_units:
        for k, val in data_units.iteritems():
            data[k] *= UREG[str(val)]  # apply units
    return data


def _read_header(f, header_param):
    """
    Read and parse data from 1st line of a file.

    :param f: :func:`file` or :class:`~StringIO.StringIO` object from which to
        read 1st line.
    :type f: file
    :param header_param: Parameters used to parse the data from the header.
        Contains "delimiter" and "fields".
    :type header_param: dict
    :returns: Dictionary of data read from header.
    :rtype: dict
    :raises: :exc:`~carousel.core.exceptions.UnnamedDataError`

    The **header_param** argument contains keys to read the 1st line of **f**.
    If "delimiter" is ``None`` or missing, the default delimiter is a comma,
    otherwise "delimiter" can be any single character, integer or sequence of
    ``int``.

    * single character -- a delimiter
    * single integer -- uniform fixed width
    * sequence of ``int`` -- fixed widths, the number of fields should \
        correspond to the length of the sequence.

    The "fields" key is a list of (parameter-name, parameter-type[, parameter-
    units]) lists.
    """
    # default delimiter is a comma, can't be None
    header_delim = str(header_param.get('delimiter', ','))
    # don't allow unnamed fields
    if 'fields' not in header_param:
        raise UnnamedDataError(f.name)
    header_fields = {field[0]: field[1:] for field in header_param['fields']}
    # header_names can't be generator b/c DictReader needs list, and can't be
    # dictionary b/c must be same order as 'fields' to match data readby csv
    header_names = [field[0] for field in header_param['fields']]
    # read header
    header_str = StringIO(f.readline())  # read the 1st line
    # use csv because it will preserve quoted fields with commas
    # make a csv.DictReader from header string, use header names for
    # fieldnames and set delimiter to header delimiter
    header_reader = csv.DictReader(header_str, header_names,
                                   delimiter=header_delim,
                                   skipinitialspace=True)
    data = header_reader.next()  # parse the header dictionary
    # iterate over items in data
    for k, v in data.iteritems():
        header_type = header_fields[k][0]  # spec'd type
        # whitelist header types
        if isinstance(header_type, basestring):
            if header_type.lower().startswith('int'):
                header_type = int  # coerce to integer
            elif header_type.lower().startswith('long'):
                header_type = long  # coerce to long integer
            elif header_type.lower().startswith('float'):
                header_type = float  # to floating decimal point
            elif header_type.lower().startswith('str'):
                header_type = str  # coerce to string
            elif header_type.lower().startswith('bool'):
                header_type = bool  # coerce to boolean
            else:
                raise TypeError('"%s" is not a supported type.' % header_type)
            # WARNING! Use of `eval` considered harmful. `header_type` is read
            # from JSON file, not secure input, could be used to exploit system
        data[k] = header_type(v)  # cast v to type
        # check for units in 3rd element
        if len(header_fields[k]) > 1:
            units = UREG[str(header_fields[k][1])]  # spec'd units
            data[k] = data[k] * units  # apply units
    return data


def _apply_units(data_data, data_units, fname):
    """
    Apply units to data.

    :param data_data: NumPy structured array with data from fname.
    :type data_data: :class:`numpy.ndarray`
    :param data_units: Units of fields in data_data.
    :type data_units: dict
    :param fname: Name of file from which data_data was read.
    :type fname: str
    :returns: Dictionary of data with units applied.
    :rtype: dict
    :raises: :exc:`~carousel.core.exceptions.UnnamedDataError`
    """
    data_names = data_data.dtype.names
    # raise error if NumPy data doesn't have names
    if not data_names:
        raise UnnamedDataError(fname)
    data = dict.fromkeys(data_names)  # dictionary of data read by NumPy
    # iterate over data read by NumPy
    for data_name in data_names:
        if data_name in data_units:
            # if units specified in parameters, then convert to string
            units = str(data_units[data_name])
            data[data_name] = data_data[data_name] * UREG[units]
        elif np.issubdtype(data_data[data_name].dtype, str):
            # if no units specified and is string
            data[data_name] = data_data[data_name].tolist()
        else:
            data[data_name] = data_data[data_name]
    return data


def _utf8_list_to_ascii_tuple(utf8_list):
    """
    Convert unicode strings in a list of lists to ascii in a list of tuples.

    :param utf8_list: A nested list of unicode strings.
    :type utf8_list: list
    """
    for n, utf8 in enumerate(utf8_list):
        utf8_list[n][0] = str(utf8[0])
        utf8_list[n][1] = str(utf8[1])
        utf8_list[n] = tuple(utf8)


class ParameterizedXLS(XLRDReader):
    """
    Concatenate data from parameterized sheets.

    :param parameters: Parameterization information.

    All data in parameterized sheets must be vectors of only numbers.
    """
    def __init__(self, parameters):
        #: parameterizaton information
        self.parameterization = parameters
        new_parameters = {}  # empty dict for sheet parameters
        parameter_sheets = self.parameterization['parameter']['sheets']
        for n, sheet in enumerate(parameter_sheets):
            new_parameters[sheet] = {}  # empty dictionary for sheet data
            for k, v in self.parameterization['data'].iteritems():
                new_parameters[sheet][k + '_' + str(n)] = v
        super(ParameterizedXLS, self).__init__(new_parameters)
        # filename is instance attribute of XLRDReader

    def load_data(self, filename, *args, **kwargs):
        """
        Load parameterized data from different sheets.
        """
        # load parameterized data
        data = super(ParameterizedXLS, self).load_data(filename)
        # add parameter to data
        parameter_name = self.parameterization['parameter']['name']
        parameter_values = self.parameterization['parameter']['values']
        parameter_units = str(self.parameterization['parameter']['units'])
        data[parameter_name] = parameter_values * UREG[parameter_units]
        # number of sheets
        num_sheets = len(self.parameterization['parameter']['sheets'])
        # parse and concatenate parameterized data
        for key in self.parameterization['data']:
            units = str(self.parameterization['data'][key].get('units')) or ''
            datalist = []
            for n in xrange(num_sheets):
                k = key + '_' + str(n)
                datalist.append(data[k].reshape((1, -1)))
                data.pop(k)  # remove unused data keys
            data[key] = np.concatenate(datalist, axis=0) * UREG[units]
        return data

    def apply_units_to_cache(self, data):
        """
        Apply units to :class:`ParameterizedXLS` data reader.
        """
        # parameter
        parameter_name = self.parameters['parameter']['name']
        parameter_units = str(self.parameters['parameter']['units'])
        data[parameter_name] *= UREG[parameter_units]
        # data
        self.parameters.pop('parameter')
        return super(ParameterizedXLS, self).apply_units_to_cache(data)


class MixedTextXLS(XLRDReader):
    """
    Get parameters from cells mixed with text by matching regex pattern.

    :raises: :exc:`~carousel.core.exceptions.MixedTextNoMatchError`

    Use this reader for spreadsheets that have numerical data mixed with text.
    It uses the same parameter file as :class:`XLRDReader` with two additional
    keys: "pattern" and "method". The "pattern" must be a valid regex pattern.
    Remember to escape backslashes. The "method" must be one of the following
    regex methods from :mod:`re`:

        * :func:`~re.match`
        * :func:`~re.search`
        * :func:`~re.split`
        * :func:`~re.findall`

    The default method is :func:`re.search` and the default pattern searches
    for any number represented by the FORTRAN formatters "%e", "%E", "%f" or
    "%g". This will find one number in any of the formats anywhere in the text
    of the cell(s) read.

    Example::

        {
          "Sheet1": {
            "sigma_bypass_diode": {
              "range": [15, 1],
              "pattern":
                "\\w+ = ([-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][-+]?\\d+)?)",
              "method": "match"
            },
            "B_bypass_diode": {
              "range": [16, 1],
              "method": "findall"
            },
            "C_bypass_diode": {
              "range": [17, 1],
              "pattern": "\((\\d+), (\\d+), (\\d+)\)",
              "method": "search"
            },
            "cov_bypass_diode": {
              "range": [18, 1],
              "pattern": "[,;]",
              "method": "split"
            }
          }
        }

    These examples all read from "Sheet1". The first example matches one or
    more alphanumeric characters at the beginning of the string set equal to an
    integer, decimal or number in scientific notation, such as "Std = 0.4985"
    from cell B16. The second example finds all numbers matching the default
    pattern in cell B17. The third example searches for 3 integers in
    parenthesis separated by commas anywhere in cell B18. The last example
    splits a string delimited by commas and semicolons in cell B19.

    If no match is found then
    :exc:`~carousel.core.exceptions.MixedTextNoMatchError`
    is raised. Only numbers can be read, and any single-dimensions will be
    squeezed out. For example scalars will become 0-d arrays.
    """

    def load_data(self, filename, *args, **kwargs):
        """
        Load text data from different sheets.
        """
        # load text data
        data = super(MixedTextXLS, self).load_data(filename)
        # iterate through sheets in parameters
        for sheet_params in self.parameters.itervalues():
            # iterate through the parameters on each sheet
            for param, pval in sheet_params.iteritems():
                pattern = pval.get('pattern', EFG_PATTERN)  # get pattern
                re_meth = pval.get('method', 'search')  # get re method
                # whitelist re methods, getattr could be considered harmful
                if re_meth in RE_METH:
                    re_meth = getattr(re, pval.get('method', 'search'))
                else:
                    msg = 'Only', '"%s", ' * len(RE_METH) % tuple(RE_METH)
                    msg += 'regex methods are allowed.'
                    raise AttributeError(msg)
                # if not isinstance(data[param], basestring):
                #     re_meth = lambda p, dp: [re_meth(p, d) for d in dp]
                match = re_meth(pattern, data[param])  # get matches
                if match:
                    try:
                        match = match.groups()
                    except AttributeError:
                        match = [m.groups() for m in match]
                    npdata = np.array(match, dtype=float).squeeze()
                    data[param] = npdata * UREG[str(pval.get('units') or '')]
                else:
                    raise MixedTextNoMatchError(re_meth, pattern, data[param])
        return data
