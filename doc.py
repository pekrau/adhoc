""" Adhoc: Simple web application for task execution.

Documentation HTML page interface.
"""

import os.path

from .method_mixin import *
from .representation import HtmlRepresentation


class GET_Doc(MethodMixin, GET):
    "Documentation page."

    outreprs = (HtmlRepresentation,)

    def get_data(self, resource, request, application):
        data = self.get_data_basic(resource, request, application)
        filename = resource.variables['filename']
        filename = os.path.basename(filename) # Security
        data['title'] = filename.replace('_', ' ')
        filepath = os.path.join(configuration.DOCS_DIR, filename) + '.md'
        try:
            outfile = open(filepath)
        except IOError:
            raise HTTP_NOT_FOUND
        data['descr'] = outfile.read()
        outfile.close()
        return data
