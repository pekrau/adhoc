""" Adhoc: Simple web application for task execution.

Produce the documentation for the web resource API by introspection.
"""

from wrapid.documentation import *

from .base import *


class AdhocDocumentation(MethodMixin, GET_Documentation):
    "Return a static documentation page."

    dirpath       = configuration.DOCS_DIR
    cache_control = 'max-age=300'

    outreprs = [JsonRepresentation,
                HtmlRepresentation]


class ApiDocumentationHtmlRepresentation(ApiDocumentationHtmlMixin,
                                         HtmlRepresentation):
    "Apply Adhoc look to the documentation."

    stylesheets = ['static/standard.css']


class AdhocApiDocumentation(MethodMixin, GET_ApiDocumentation):
    "Produce the documentation for the web resource API by introspection."

    outreprs = [JsonRepresentation,
                ApiDocumentationHtmlRepresentation]
