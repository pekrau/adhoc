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

    def get_data_resource(self, resource, request, application):
        return dict(resource='Home',
                    descr=open(configuration.README_FILE).read())
