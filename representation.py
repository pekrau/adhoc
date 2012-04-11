""" Adhoc: Simple web application for task execution.

General representation classes.
"""

from wrapid.html_representation import *
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration


class HtmlRepresentation(BaseHtmlRepresentation):
    "HTML representation of the resource."

    logo        = 'static/adhoc.png'
    favicon     = 'static/favicon.ico'
    stylesheets = ['static/standard.css']
    scripts     = ['static/jquery-1.6.4.min.js',
                   'static/jquery.localtime-0.5.js']

    def get_head(self):
        head = super(HtmlRepresentation, self).get_head()
        try:
            refresh = self.data['refresh']
        except KeyError:
            pass
        else:
            url = "%s?refresh=%s" % (self.data['href'],
                                     min(configuration.MAX_REFRESH,
                                         configuration.REFRESH_FACTOR*refresh))
            head.append(META(http_equiv='Refresh',
                             content="%s; url=%s" % (refresh, url)))
        return head

    def get_icon(self, name):
        return IMG(src=self.get_url('static', "%s.png" % name),
                   alt=name, title=name, width=16, height=16)


class FormHtmlRepresentation(FormHtmlMixin, HtmlRepresentation):
    "HTML representation of the form page for data input."
    pass
