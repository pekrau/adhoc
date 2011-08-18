""" Adhoc web resource.

Configuration settings.
"""

import logging
import os
import sys
import socket
import urllib
import hashlib
import time
import json

VERSION = '1.0'

logging.basicConfig(level=logging.DEBUG)


DATE_ISO_FORMAT = "%Y-%m-%d"
TIME_ISO_FORMAT = "%H:%M:%S"
DATETIME_ISO_FORMAT = "%sT%sZ" % (DATE_ISO_FORMAT, TIME_ISO_FORMAT)

HOSTNAME = socket.gethostname()

# The site module must define the following global variables:
# SALT        password encryption salt
# URL_ROOT    root of URL for web site
# DATA_DIR    directory for adhoc data
# PYTHON      path to python interpreter
MODULENAME = "adhoc.site_%s" % HOSTNAME
try:
    __import__(MODULENAME)
except ImportError:
    raise NotImplementedError("host %s" % HOSTNAME)
else:
    module = sys.modules[MODULENAME]
    for key in dir(module):
        if key.startswith('_'): continue
        globals()[key] = getattr(module, key)

URL_BASE = "http://%s" % URL_ROOT

SOURCE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(SOURCE_DIR, 'static')
TASK_SCRIPT = os.path.join(SOURCE_DIR, 'task.py')

ADHOC_FILE = os.path.join(DATA_DIR, 'adhoc.sqlite3')
DB_DIR = os.path.join(DATA_DIR, 'db')
TASK_DIR = os.path.join(DATA_DIR, 'task')

TOOLS = []
TOOLS_LOOKUP = dict()

def add_tool(name, function, description, version):
    TOOLS.append(dict(name=name,
                      function=function,
                      description=description,
                      version=version))
    TOOLS_LOOKUP[name] = function

def get_teams():
    """Return the set of teams.
    NOTE: a team name must *not* contain any blanks!"""
    infile = open('/var/local/adhoc/teams.json')
    try:
        return set(json.load(infile))
    finally:
        infile.close()

def get_url(*parts, **params):
    "Return the absolute URL given the path parts."
    url = '/'.join([URL_BASE] + list(parts))
    if params:
        url += '?' + urllib.urlencode(params)
    return url

def get_password_hexdigest(password):
    md5 = hashlib.md5()
    md5.update(SALT)
    md5.update(password)
    return md5.hexdigest()

def get_static_path(filename):
    path = os.path.normpath(os.path.join(STATIC_DIR, filename))
    if not path.startswith(STATIC_DIR):
        raise ValueError('access outside of static directory')
    return path

def now():
    return time.strftime(DATETIME_ISO_FORMAT, time.gmtime())

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
