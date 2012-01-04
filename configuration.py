""" Adhoc web resource: simple bioinformatics tasks.

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

NAME = 'Adhoc'
VERSION = '2.2'
REALM = 'adhoc'

DEBUG = False                           # May be changed by site module

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

REFRESH_FACTOR = 2.0
MAX_REFRESH = 65.0
DEFAULT_MAX_TASKS = 200

PYTHON = '/usr/bin/python'

DATA_DIR = '/var/local/adhoc'
SALT = 'default123'

TEST_ROOT = '/adhoc'
TEST_ACCOUNT = 'test'
TEST_PASSWORD = 'abc123'

#----------------------------------------------------------------------
# Do not change anything below this section.
#----------------------------------------------------------------------
# The 'site_XXX' module must define paths to tool executables.
# It may redefine any of the above global variables.
HOSTNAME = socket.gethostname()
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
#----------------------------------------------------------------------


if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


CREATED = 'created'
WAITING = 'waiting'
EXECUTING = 'executing'
FINISHED = 'finished'
FAILED = 'failed'
KILLED = 'killed'
STATUSES = set([CREATED, WAITING, EXECUTING, FINISHED, FAILED, KILLED])
DYNAMIC_STATUSES = set([CREATED, WAITING, EXECUTING])
STATIC_STATUSES = set([FINISHED, FAILED, KILLED])

SOURCE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(SOURCE_DIR, 'static')
DOCS_DIR = os.path.join(SOURCE_DIR, 'docs')
EXECUTE_SCRIPT = os.path.join(SOURCE_DIR, 'execute.py')

MASTER_DBFILE = os.path.join(DATA_DIR, 'adhoc.sql3')
DB_DIR = os.path.join(DATA_DIR, 'db')
TASK_DIR = os.path.join(DATA_DIR, 'task')

TOOLS = []                              # List of lists; first item is section
TOOLS_LOOKUP = dict()


def add_tool(family, name, function):
    if name in TOOLS_LOOKUP:
        raise ValueError("tool '%s' already added" % name)
    for tools in TOOLS:
        if tools[0] == family:
            tools.append(dict(family=family, name=name, function=function))
            break
    else:
        tools = [family, dict(family=family, name=name, function=function)]
        TOOLS.append(tools)
    TOOLS_LOOKUP[name] = function

def get_teams():
    """Return the list of teams.
    NOTE: a team name must *not* contain any blanks!"""
    infile = open(os.path.join(DATA_DIR, 'teams.json'))
    try:
        return [str(t) for t in json.load(infile)]
    finally:
        infile.close()

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
    return time.strftime(DATETIME_FORMAT, time.gmtime())

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
