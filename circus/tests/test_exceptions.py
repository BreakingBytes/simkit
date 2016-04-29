"""
test circus exceptions
"""

from circus.core import logging
from circus.core.circus_exceptions import (
    UnnamedDataError, PVSimTimezoneError, DuplicateRegItemError
)
from nose.tools import raises, eq_

LOGGER = logging.getLogger(__name__)


@raises(UnnamedDataError)
def test_unnamed_data_error():
    filename = 'myfile.test'
    try:
        raise UnnamedDataError(filename)
    except UnnamedDataError as err:
        LOGGER.debug('error: %s', err.__class__)
        eq_(err.filename, filename)
        LOGGER.debug('filename: %s', err.filename)
        eq_(err.message, 'Data read from "%s" without names.' % filename)
        LOGGER.debug('message: %s', err.message)
        raise err


@raises(PVSimTimezoneError)
def test_timezone_error():
    timezone = 'US/Pacific'
    try:
        raise PVSimTimezoneError(timezone)
    except PVSimTimezoneError as err:
        LOGGER.debug('error: %s', err.__class__)
        eq_(err.timezone, timezone)
        LOGGER.debug('timezone: %s', err.timezone)
        eq_(err.message, 'Incorrect timezone format: "%s".' % timezone)
        LOGGER.debug('message: %s', err.message)
        raise err


@raises(DuplicateRegItemError)
def test_duplicate_registry_item_error():
    duplicate_keys = {'foo', 'bar'}
    try:
        raise DuplicateRegItemError(duplicate_keys)
    except DuplicateRegItemError as err:
        LOGGER.debug('error: %s', err.__class__)
        eq_(err.duplicate_keys, duplicate_keys)
        LOGGER.debug('duplicate_keys: %s', err.duplicate_keys)
        eq_(err.message,
            "Duplicate data can't be registered:\n\t%s" %
            '\n\t'.join(duplicate_keys))
        LOGGER.debug('message: %s', err.message)
        raise err
