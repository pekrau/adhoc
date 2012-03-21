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

    def get_login(self):
        "Login as anonymous depends on whether present in database or not."
        login = self.data.get('login')
        if login:
            result = DIV('Logged in as: ',
                         A(login, href=self.get_url('account', login)))
        else:
            result = I('Not logged in')
        if not login or login == 'anonymous':
            url = self.data.get('href', self.get_url())
            result = TABLE(TR(TD(result)),
                           TR(TD(FORM(self.get_button('Login'),
                                      INPUT(type='hidden',
                                            name='href', value=url),
                                      method='GET',
                                      action=self.get_url('login')))))
        return result

    def get_icon(self, name):
        return IMG(src=self.get_url('static', "%s.png" % name),
                   alt=name, title=name, width=16, height=16)


class FormHtmlRepresentation(FormHtmlMixin, HtmlRepresentation):
    "HTML representation of the form page for data input."
    pass
