""" Adhoc: Simple web application for task execution.

Apache WSGI interface using the 'wrapid' package.
"""

import wrapid
assert wrapid.__version__ in ('12.5', '12.7')
from wrapid.application import Application
from wrapid.login import Login
from wrapid.file import File

import adhoc
from adhoc import configuration
from adhoc.home import *
from adhoc.account import *
from adhoc.task import *
from adhoc.about import *
from adhoc.documentation import *


application = Application(name='Adhoc',
                          version=adhoc.__version__,
                          host=configuration.HOST,
                          debug=configuration.DEBUG)

# Home
application.add_resource('/',
                         name='Home',
                         GET=Home)

# 'Static resources; accessed often, keep at beginning of the chain.
class StaticFile(File):
    "Return the specified file from a predefined server directory."
    dirpath       = configuration.STATIC_DIR
    cache_control = 'max-age=300'

application.add_resource('/static/{filepath:path}',
                         name='File',
                         GET=StaticFile)

# Task resources
application.add_resource('/tasks',
                         name='Task list',
                         GET=Tasks)
application.add_resource('/tasks/{account}',
                         name='Task list account',
                         GET=TasksAccount)
application.add_resource('/task/{iui:uuid}',
                         name='Task',
                         GET=Task,
                         DELETE=DeleteTask)
application.add_resource('/task/{iui:uuid}/status',
                         name='Task status',
                         GET=TaskStatus)
application.add_resource('/task/{iui:uuid}/query',
                         name='Task query',
                         GET=TaskQuery)
application.add_resource('/task/{iui:uuid}/output',
                         name='Task output',
                         GET=TaskOutput)

# Account resources
application.add_resource('/accounts',
                         name='Account list',
                         GET=Accounts)
application.add_resource('/account/{account}',
                         name='Account',
                         GET=Account)

# Documentation resources
application.add_resource('/about',
                         name='Documentation About',
                         GET=About)
application.add_resource('/doc/API',
                         name='Documentation API',
                         GET=AdhocApiDocumentation)
application.add_resource('/doc/{filename}',
                         name='Documentation file',
                         GET=AdhocDocumentation)

# Login and account resources
class LoginAccount(Login):
    "Perform login to an account. Basic Authentication."
    def get_account(self, name, password):
        return configuration.users.get_account(name, password)

application.add_resource('/login',
                         name='Login',
                         GET=LoginAccount)

# Tools: BLAST
import adhoc.blast
adhoc.blast.setup(application)
