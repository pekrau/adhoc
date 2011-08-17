""" Adhoc web resource.

Apache WSGI interface using the 'wireframe' package.
"""

import wireframe.application

from adhoc.webresource import *
from adhoc.home import *
from adhoc.account import *

import adhoc.blast

application = wireframe.application.Application(human_debug_output=True)

application.add_dispatcher('template:/?', Home)
application.add_dispatcher('template:/static/{filename}', Static)
application.add_dispatcher('template:/accounts', Accounts)
application.add_dispatcher('template:/account/{name}', Account)
application.add_dispatcher('template:/account/{name}/edit', AccountEdit)
application.add_dispatcher('template:/account', AccountCreate)
application.add_dispatcher('template:/tasks', Tasks)
application.add_dispatcher('template:/tasks/{account}', AccountTasks)
application.add_dispatcher('template:/task/{iui}', TaskDisplay)
application.add_dispatcher('template:/task/{iui}/status', TaskStatus)
application.add_dispatcher('template:/task/{iui}/output', TaskOutput)

adhoc.blast.setup(application)
