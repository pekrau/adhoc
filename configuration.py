""" Adhoc: Simple web application for task execution.

Configuration settings.
"""

import logging
import os
import sys
import socket


DEBUG = False

DATA_DIR = '/var/local/adhoc'

HOST = dict(title='SciLifeLab tools',
            href='http://localhost/')

DEFAULT_QUOTA_NTASKS = 200

REFRESH_FACTOR = 2.0
MAX_REFRESH = 65.0

# Path to Python executable
PYTHON = '/usr/bin/python'

# BLAST executables location and version
BLAST_PATH = '/usr/local/bin'
BLAST_VERSION = 'NCBI 2.2.25+ 32bit'

# Fallback user account interface; should be overriden by proper implementation
import fallback_users as users

# Specify string template for user account editing, if available
ACCOUNT_BASE_URL_TEMPLATE = None


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


CREATED   = 'created'
WAITING   = 'waiting'
EXECUTING = 'executing'
FINISHED  = 'finished'
FAILED    = 'failed'
KILLED    = 'killed'
STATUSES         = set([CREATED, WAITING, EXECUTING, FINISHED, FAILED, KILLED])
DYNAMIC_STATUSES = set([CREATED, WAITING, EXECUTING])
STATIC_STATUSES  = set([FINISHED, FAILED, KILLED])

SOURCE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(SOURCE_DIR, 'static')
DOCS_DIR = os.path.join(SOURCE_DIR, 'docs')
EXECUTE_SCRIPT = os.path.join(SOURCE_DIR, 'execute.py')

README_FILE = os.path.join(SOURCE_DIR, 'README.md')
MASTER_DB_FILE = os.path.join(DATA_DIR, 'master.sql3')
DB_DIR = os.path.join(DATA_DIR, 'db')
TASK_DIR = os.path.join(DATA_DIR, 'task')


def get_account_quotas(account):
    "Get the quotas dictionary from the account dictionary, or defaults."
    try:
        return account['properties']['Adhoc']['quotas']
    except KeyError:
        return dict(ntasks=DEFAULT_QUOTA_NTASKS)


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
