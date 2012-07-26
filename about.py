""" Adhoc: Simple web application for task execution.

About page, describing the software of the system.
"""

from .base import *


class About(MethodMixin, GET):
    "About page, describing the system software."

    outreprs = [JsonRepresentation,
                HtmlRepresentation]

    def is_accessible(self):
        "Anyone may view the about page."
        return True

    def get_data_resource(self, request):
        return dict(resource='About',
                    descr=open(configuration.README_FILE).read())
