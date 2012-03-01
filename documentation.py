""" Adhoc: Simple web application for task execution.

Produce the documentation for the web resource API by introspection.
"""

from wrapid.documentation import *

from .representation import *
from .method_mixin import MethodMixin


class GET_AdhocDocumentation(MethodMixin, GET_Documentation):
    "Return a static documentation page."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                HtmlRepresentation]


class ApiDocumentationHtmlRepresentation(ApiDocumentationHtmlMixin,
                                         HtmlRepresentation):
    "Apply Adhoc look to the documentation."

    stylesheets = ['static/standard.css']


class GET_AdhocApiDocumentation(MethodMixin, GET_ApiDocumentation):
    "Produce the documentation for the web resource API by introspection."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                ApiDocumentationHtmlRepresentation]
