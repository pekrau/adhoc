""" Adhoc: Simple web application for task execution.

Apache WSGI interface using the 'wrapid' package.
"""

import wrapid
from wrapid.application import Application
from wrapid.login import GET_Login
from wrapid.file import GET_File

import adhoc
from adhoc import configuration
from adhoc.home import *
from adhoc.account import *
from adhoc.task import *
from adhoc.documentation import *

# Package dependency
assert wrapid.__version__ == '12.4'


application = Application(name='Adhoc',
                          version=adhoc.__version__,
                          host=configuration.HOST,
                          debug=configuration.DEBUG)

# Home
application.add_resource('/', name='Home',
                         GET=GET_Home)

# 'Static resources; accessed often, keep at beginning of the chain.
class GET_File_static(GET_File):
    dirpath       = configuration.STATIC_DIR
    cache_control = 'max-age=300'

application.add_resource('/static/{filename}', name='File',
                         GET=GET_File_static)

# Task resources
application.add_resource('/tasks', name='Task list',
                         GET=GET_Tasks)
application.add_resource('/tasks/{account}', name='Task list account',
                         GET=GET_TasksAccount)
application.add_resource('/task/{iui:uuid}', name='Task',
                         GET=GET_Task,
                         DELETE=DELETE_Task)
application.add_resource('/task/{iui:uuid}/status', name='Task status',
                         GET=GET_TaskStatus)
application.add_resource('/task/{iui:uuid}/query', name='Task query',
                         GET=GET_TaskQuery)
application.add_resource('/task/{iui:uuid}/output', name='Task output',
                         GET=GET_TaskOutput)

# Account resources
application.add_resource('/accounts', name='Account list',
                         GET=GET_Accounts)
application.add_resource('/account/{account}', name='Account',
                         GET=GET_Account)

# Documentation resources
application.add_resource('/doc/API', name='Documentation API',
                         GET=GET_AdhocApiDocumentation)
application.add_resource('/doc/{filename}', name='Documentation file',
                         GET=GET_AdhocDocumentation)

# Login and account resources
class GET_Login_account(GET_Login):
    def get_account(self, name, password):
        return configuration.users.get_account(name, password)

application.add_resource('/login', name='Login',
                         GET=GET_Login_account)

# Tools: BLAST
import adhoc.blast
adhoc.blast.setup(application)
