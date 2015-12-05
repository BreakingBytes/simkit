# -*- coding: utf-8 -*-
"""
Exceptions for Circus.
"""


class CircusException(Exception):
    """
    Base exception class for pvmismatch.
    """
    pass


class UnnamedDataError(CircusException):
    """
    An exception raised when a parameter is loaded without a name.

    :param filename: The name of the file from which the data was loaded.
    :type filename: str
    """
    def __init__(self, filename):
        self.args = filename
        self.message = str(self)

    def __str__(self):
        error_message = 'Data read from %s without names.' % self.args
        return error_message


class PVSimTimezoneError(CircusException):
    """
    An exception raised when PVSim timezone is in unexpected format.

    :param timezone: The timezone string that was read from the PVSim file.
    :type timezone: str
    """
    def __init__(self, timezone):
        self.args = timezone
        self.message = str(self)

    def __str__(self):
        error_message = 'Incorrect timezone format: "%s".' % self.args
        return error_message


class DuplicateRegItemError(CircusException):
    """
    An exception raised when duplicate data is registered.

    :param keys: Keys of the duplicate data.
    :type keys: set
    """
    def __init__(self, keys):
        self.args = keys
        self.message = str(self)

    def __str__(self):
        error_message = ['Duplicate data can\'t be registered:',
                        '\n\t"%s".' % ', '.join(self.args)]
        return '\n'.join(error_message)


class MismatchRegMetaKeysError(CircusException):
    """
    An exception raised when meta with mismatched keys is registered.

    :param keys: Keys of the mismatched meta.
    :type keys: set
    """
    def __init__(self, keys):
        self.args = keys
        self.message = str(self)

    def __str__(self):
        error_message = ['Meta must be a subset of registry:',
                        '\n\t"%s".' % ', '.join(self.args)]
        return '\n'.join(error_message)


class UncertaintyPercentUnitsError(CircusException):
    """
    An exception raised when uncertainty doesn't have percent units.

    :param key: Key of uncertainty that doesn't have percent units.
    :type key: str
    :param units: Units of the uncertainty key that doesn't have percent units.
    :type units: str
    """
    def __init__(self, key, units):
        self.args = key, units
        self.message = str(self)

    def __str__(self):
        error_message = ['Uncertainty can only have units of percent (%%),',
                        'but "%s" has units of "%s" instead.' % self.args]
        return ' '.join(error_message)


class UncertaintyBoundsUnitsError(CircusException):
    """
    An exception raised when the lower and upper uncertainty bounds do not have
    matching units, which should both be percent, otherwise
    :exc:`UncertaintyPercentUnitsError` is raised.

    :param key: Uncertainty key with mismatched lower and upper bounds.
    :type key: str
    :param lo_units: Units of lower uncertainty bound.
    :type lo_units: :mod:`quantities`
    :param up_units: Units of upper uncertainty bound
    :type up_units: :mod:`quantities`
    """
    def __init__(self, key, lo_units, up_units):
        self.args = key, lo_units.dimensionality, up_units.dimensionality
        self.message = str(self)

    def __str__(self):
        error_message = ['Uncertainty lower and upper bounds must both have',
                         'units of percent (%%), but "%s" has units of "%s"',
                         'for the lower bound and "%s" for the upper bound.']
        return ' '.join(error_message) % self.args


class CircularDependencyError(Exception):
    """
    Topological sort cyclic error.
    """
    def __init__(self, keys):
        self.args = keys
        self.message = self.__str__

    def __str__(self):
        return 'Not a DAG. These keys are cyclic:\n\t%s' % str(self.args)


class MixedTextNoMatchError(Exception):
    """
    No match in mixed text data source error.
    """
    def __init__(self, re_meth, pattern, data):
        self.args = re_meth, pattern, data
        self.message = self.__str__

    def __str__(self):
        return 'No match using regex "%s" with "%s" in "%s".' % self.args
