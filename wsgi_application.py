""" Adhoc: Simple web application for task execution.

Apache WSGI interface using the 'wrapid' package.
"""

import wrapid
from wrapid.resource import Resource
from wrapid.application import Application
from wrapid.login import GET_Login
from wrapid.static import GET_Static

import adhoc
from adhoc import configuration
from adhoc.home import *
from adhoc.account import *
from adhoc.task import *
from adhoc.documentation import *

# Package dependency
assert wrapid.__version__ == '12.3'


application = Application(name='Adhoc',
                          version=adhoc.__version__,
                          host=configuration.HOST,
                          debug=configuration.DEBUG)


# Home
application.append(Resource('/',
                            type='Home',
                            GET=GET_Home))

# 'Static resources; accessed often, keep at beginning of the chain.
application.append(Resource('/static/{filename}',
                            type='File',
                            GET=GET_Static(configuration.STATIC_DIR,
                                           cache_control='max-age=300')))

# Task resources
application.append(Resource('/tasks',
                            type='Task list',
                            GET=GET_Tasks))
application.append(Resource('/tasks/{account}',
                            type='Task list account',
                            GET=GET_TasksAccount))
application.append(Resource('/task/{iui:uuid}',
                            type='Task',
                            GET=GET_Task,
                            DELETE=DELETE_Task))
application.append(Resource('/task/{iui:uuid}/status',
                            type='Task status',
                            GET=GET_TaskStatus))
application.append(Resource('/task/{iui:uuid}/query',
                            type='Task query',
                            GET=GET_TaskQuery))
application.append(Resource('/task/{iui:uuid}/output',
                            type='Task output',
                            GET=GET_TaskOutput))

# Account resources
application.append(Resource('/accounts',
                            type='Account list',
                            GET=GET_Accounts))
application.append(Resource('/account/{account}',
                            type='Account',
                            GET=GET_Account))

# Documentation resources
application.append(Resource('/doc/API',
                            type='Documentation API',
                            GET=GET_AdhocApiDocumentation))
application.append(Resource('/doc/{filename}',
                            type='Documentation file',
                            GET=GET_AdhocDocumentation(configuration.DOCS_DIR)))

# Other resources
application.append(Resource('/login',
                            type='Login',
                            GET=GET_Login(configuration.users.get_account)))

# Tools: BLAST
import adhoc.blast
adhoc.blast.setup(application)
