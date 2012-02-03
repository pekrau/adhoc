""" Adhoc: Simple web application for task execution.

Home page.
"""

from .method_mixin import *
from .representation import *


class GET_Home(MethodMixin, GET):
    "The Adhoc home page."

    outreprs = (JsonRepresentation,
                TextRepresentation,
                HtmlRepresentation)

    def get_data(self, resource, request, application):
        data = self.get_data_basic(resource, request, application)
        data['title'] = "%s %s" % (application.name, application.version)
        try:
            data['descr'] = open(configuration.README_FILE).read()
        except IOError:
            data['descr'] = 'Adhoc: Simple web application for task execution'
        return data
