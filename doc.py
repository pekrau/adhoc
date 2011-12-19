""" Adhoc web resource: simple bioinformatics tasks.

Documentation HTML page interface.
"""

import os.path

from wrapid.resource import *

from . import configuration
from .method_mixin import *
from .html_representation import HtmlRepresentation


class GET_Doc(GET_Mixin, GET):
    "Adhoc documentation page."

    def __init__(self):
        super(GET_Doc, self).__init__(
            outreprs=[HtmlRepresentation()],
            descr=self.__doc__)

    def add_data(self, data, resource, request, application):
        filename = resource.variables['filename']
        filename = os.path.basename(filename) # Security
        data['title'] = filename.replace('_', ' ')
        filepath = os.path.join(configuration.DOCS_DIR, filename) + '.mkd'
        try:
            outfile = open(filepath)
        except IOError:
            raise HTTP_NOT_FOUND
        data['descr'] = outfile.read()
        outfile.close()
