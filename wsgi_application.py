""" Adhoc: Simple web application for task execution.

Apache WSGI interface using the 'wrapid' package.
"""

import wrapid
from wrapid.application import Application
from wrapid.get_static import GET_Static
from wrapid.get_documentation import GET_Documentation

import adhoc
from adhoc import configuration
from adhoc.home import *
from adhoc.doc import *
from adhoc.login import *               # XXX Replace when WhoYou implemented
from adhoc.account import *
from adhoc.task import *

# Package dependency
assert wrapid.__version__ == '2.0'


class Adhoc(Application):
    version = adhoc.__version__
    debug   = configuration.DEBUG

application = Adhoc()

# Home
application.append(Resource('/',
                            type='Home',
                            GET=GET_Home()))

# 'Static resources; accessed often, keep at beginning of the chain.
application.append(Resource('/static/{filename}',
                            type='File',
                            GET=GET_Static(configuration.STATIC_DIR,
                                           cache_control='max-age=3600')))

# Task resources
application.append(Resource('/tasks',
                            type='Task list',
                            GET=GET_Tasks()))
application.append(Resource('/tasks/{account}',
                            type='Task list account',
                            GET=GET_Tasks()))
application.append(Resource('/task/{iui:uuid}',
                            type='Task',
                            GET=GET_Task(),
                            DELETE=DELETE_Task()))
application.append(Resource('/task/{iui:uuid}/status',
                            type='Task status',
                            GET=GET_TaskStatus()))
application.append(Resource('/task/{iui:uuid}/query',
                            type='Task query',
                            GET=GET_TaskQuery()))
application.append(Resource('/task/{iui:uuid}/output',
                            type='Task output',
                            GET=GET_TaskOutput()))

# Account resources
application.append(Resource('/accounts',
                            type='Account list',
                            GET=GET_Accounts()))
application.append(Resource('/account/{account}',
                            type='Account',
                            GET=GET_Account()))
application.append(Resource('/account/{account}/edit',
                            type='Account edit',
                            GET=GET_AccountEdit(),
                            POST=POST_AccountEdit()))
application.append(Resource('/account',
                            type='Account create',
                            GET=GET_AccountCreate(),
                            POST=POST_AccountCreate()))

# Tools: BLAST
import adhoc.blast
adhoc.blast.setup(application)

# Documentation resources
application.append(Resource('/doc/API',
                            type='Documentation API',
                            GET=GET_Documentation()))
application.append(Resource('/doc/{filename}',
                            type='Documentation file',
                            GET=GET_Doc()))

# Other resources
application.append(Resource('/login',
                            type='Login',
                            GET=GET_Login()))
