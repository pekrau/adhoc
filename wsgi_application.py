""" Adhoc web resource: simple bioinformatics tasks.

Apache WSGI interface using the 'wrapid' package.
"""

import wrapid.application
from wrapid.get_documentation import GET_Documentation
from wrapid.get_static import GET_Static

from adhoc import configuration
from adhoc.home import *
from adhoc.doc import *
from adhoc.login import *
from adhoc.account import *
from adhoc.task import *


application = wrapid.application.Application(name=configuration.NAME,
                                             version=configuration.VERSION,
                                             debug=configuration.DEBUG)

application.append(Resource('/', name='Home',
                            GET=GET_Home(),
                            descr='Adhoc home page.'))

# 'static' is accessed often; keep at beginning of the chain.
application.append(Resource('/static/{filename}', name='Static file',
                            GET=GET_Static(configuration.STATIC_DIR,
                                           cache_control='max-age=3600'),
                            descr='Access to a static file on the server.'))

# Task resources
application.append(Resource('/tasks', name='Tasks list',
                            GET=GET_Tasks(),
                            descr='List of tasks.'))
application.append(Resource('/tasks/{account}', name='Account tasks',
                            GET=GET_Tasks(),
                            descr='List of tasks for account.'))
application.append(Resource('/task/{iui:uuid}', name='Task',
                            GET=GET_Task(),
                            DELETE=DELETE_Task(),
                            descr='Task page.'))
application.append(Resource('/task/{iui:uuid}/status', name='Task status',
                            GET=GET_TaskStatus(),
                            descr='Task status string.'))
application.append(Resource('/task/{iui:uuid}/query', name='Task query',
                            GET=GET_TaskQuery(),
                            descr='Task query content.'))
application.append(Resource('/task/{iui:uuid}/output', name='Task output',
                            GET=GET_TaskOutput(),
                            descr='Task output content.'))

# Account resources
application.append(Resource('/accounts', name='Accounts list',
                            GET=GET_Accounts(),
                            descr='Accounts list page.'))
application.append(Resource('/account/{account}', name='Account',
                            GET=GET_Account(),
                            descr='Account page.'))
application.append(Resource('/account/{account}/edit', name='Edit account',
                            GET=GET_AccountEdit(),
                            POST=POST_AccountEdit(),
                            descr='Account editing page.'))
application.append(Resource('/account', name='Account create',
                            GET=GET_AccountCreate(),
                            POST=POST_AccountCreate()))

# Tools: BLAST
import adhoc.blast
adhoc.blast.setup(application)

# Documentation resources
application.append(Resource('/doc/API', name='API doc',
                            GET=GET_Documentation(),
                            descr='Produce this documentation of the web'
                            ' API by introspection of the source code.'))
application.append(Resource('/doc/{filename}', name='Documentation file',
                            GET=GET_Doc(),
                            descr='Access to a documentation file in'
                            ' a predetermined directory on the server.'))

application.append(Resource('/login', name='Account login',
                            GET=GET_Login(),
                            descr='Force the client to give authentication.'))
