""" Adhoc: Simple web application for task execution.

Configuration settings.
"""

import logging
import os
import sys
import socket
import urllib
import json

from wrapid.utils import get_password_hexdigest as get_pwd_hex

DEBUG = False

HOST = dict(title='SciLifeLab tools',
            href='http://localhost/')

DATA_DIR = '/var/local/adhoc'

DEFAULT_MAX_TASKS = 200

REFRESH_FACTOR = 2.0
MAX_REFRESH = 65.0

# Password encryption
SALT = 'default123'

# Path to Python executable
PYTHON = '/usr/bin/python'

# BLAST executables location and version
BLAST_PATH = '/usr/local/bin'
BLAST_VERSION = 'NCBI 2.2.25+ 32bit'


#----------------------------------------------------------------------
# Do not change anything below this.
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

README_FILE = os.path.join(SOURCE_DIR, 'README.md')
MASTER_DB_FILE = os.path.join(DATA_DIR, 'master.sql3')
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
    return get_pwd_hex(password, salt=SALT)
