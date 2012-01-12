""" Adhoc web resource: simple bioinformatics tasks.

Utility functions.
"""

import hashlib
import time

from . import configuration


def now():
    return time.strftime(configuration.DATETIME_FORMAT, time.gmtime())

def get_password_hexdigest(password):
    md5 = hashlib.md5()
    md5.update(configuration.SALT)
    md5.update(password)
    return md5.hexdigest()

def to_bool(value):
    """Convert the string value to boolean.
    Raise ValueError if not interpretable.
    """
    if not value: return False
    value = value.lower()
    if value in ('true', 't', 'on', 'yes', '1'):
        return True
    elif value in ('false', 'f', 'off', 'no', '0'):
        return False
    else:
        raise ValueError("invalid literal '%s' for boolean" % value)

def rstr(value):
    "Return str of unicode value, else same, recursively."
    if value is None:
        return None
    elif isinstance(value, unicode):
        return str(value)
    elif isinstance(value, list):
        return map(rstr, value)
    elif isinstance(value, set):
        return set(map(rstr, value))
    elif isinstance(value, dict):
        return dict([(rstr(key), rstr(value))
                     for key, value in value.iteritems()])
    else:
        return value
