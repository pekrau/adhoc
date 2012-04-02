""" Adhoc: Simple web application for task execution.

Home page.
"""

from .method_mixin import *
from .representation import *


class GET_Home(MethodMixin, GET):
    "The Adhoc home page."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                HtmlRepresentation]

    def get_data_resource(self, request):
        return dict(resource='Home',
                    descr="""
## A simple web application for task execution

The available tools are listed in the left-side panel.

It is possible to try out this web application without logging in
(i.e. using the anonymous account).
For production work, a proper login is required. The available databases
depend on which team your account is a member of. A few publicly accessible
databases are available.

Contact the administrator to obtain your own account.

For more information see the [about page](%s).
""" % request.application.get_url('about'))
