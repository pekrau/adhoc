""" Adhoc: Simple web application for task execution.

Home page.
"""

from .base import *


class Home(MethodMixin, GET):
    "The Adhoc home page."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                HtmlRepresentation]

    def get_data_resource(self, request):
        return dict(resource='Home',
                    title='Adhoc: A simple web application for task execution',
                    descr="""The available tools are listed in the left-side panel.

It is possible to try out this web application without logging in
(i.e. using the anonymous account).
For production work, a proper login is required. The available databases
depend on which team your account is a member of. A few publicly accessible
databases are available.

Contact the administrator to obtain your own account.

For more information see the [About page](%s).
""" % request.application.get_url('about'))
