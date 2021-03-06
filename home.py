""" Adhoc: Simple web application for task execution.

Home page.
"""

from .base import *


class Home(MethodMixin, GET):
    "The Adhoc home page."

    outreprs = [JsonRepresentation,
                HtmlRepresentation]

    def get_data_resource(self, request):
        return dict(resource='Home',
                    title='Adhoc: A simple web application for task execution',
                    descr="""The available tools are listed in the left-side panel.

It is possible to try out this web application without logging in
(i.e. using the anonymous account). A few publicly accessible
databases are available.

A proper login account is required for production work.
The databases available to your account depends on which team(s) the
account is a member of.

Contact the administrator to obtain your own account, and to set
the teams it is a member of.

For more information see the [About page](%s).
""" % request.application.get_url('about'))
