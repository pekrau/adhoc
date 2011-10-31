""" Adhoc web resource: simple bioinformatics tasks.

Text representation of data using Python 'pprint'.
"""

import pprint

from wrapid.resource import *


class TextRepresentation(Representation):
    "Text representation of the resource using Python 'pprint'."

    mimetype = 'text/plain'
    format = 'txt'

    def __call__(self, data):
        self.modify(data)
        response = HTTP_OK(**self.get_http_headers())
        response.append(pprint.pformat(data))
        return response

    def modify(self, data):
        pass
