""" Adhoc: Simple web application for task execution.

General representation classes.
"""

import urllib

from wrapid.response import *
from wrapid.html_representation import *
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration


class HtmlRepresentation(BaseHtmlRepresentation):
    "HTML representation of the resource."

    def prepare(self):
        "Set up the icons dictionary; requires application URL."
        self.icons = dict()
        for name in ['created', 'error', 'executing', 'failed',
                     'finished', 'killed', 'required', 'waiting', 'warning']:
            self.icons[name] = IMG(src=self.get_url('static', "%s.png" % name),
                                   title=name, width=16,height=16, klass='icon')

    def get_url(self, *segments, **query):
        "Return a URL based on the application URL."
        url = '/'.join([self.data['application']['href']] + list(segments))
        if query:
            url += '?' + urllib.urlencode(query)
        return url

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

    def get_stylesheets(self):
        return [LINK(rel='stylesheet',
                     href=self.get_url('static', 'style.css'),
                     type='text/css')]

    def get_favicon(self):
        return LINK(href=self.get_url('static', 'favicon.ico'),
                    rel='shortcut icon')

    def get_logo(self):
        return A(IMG(src=self.get_url('static', 'adhoc.png'),
                     alt=self.data['application']['name'],
                     title=self.data['application']['name']),
                 href=self.data['application']['href'])

    def get_login(self):
        loginname = self.data.get('loginname')
        if loginname and loginname != 'anonymous':
            url = self.get_url('account', loginname)
            return DIV("Logged in as: %s" % A(loginname, href=url),
                       style='white-space: nowrap;')
        else:
            return TABLE(TR(TD(I('not logged in')),
                            TD(FORM(INPUT(type='submit', value='Login'),
                                    method='GET',
                                    action=self.get_url('login')))),
                         style='white-space: nowrap;')

    def get_status(self, status):
        if status not in configuration.STATUSES:
            raise ValueError("invalid status '%s'" % status)
        return DIV(self.icons[status], SPAN(' ' + status, klass='icon'))


class FormHtmlRepresentation(HtmlRepresentation):
    "HTML representation of the form page for data input."

    submit = 'Save'

    def get_content(self):
        try:
            data = self.data['tool']
        except KeyError:
            data = self.data['form']
        required = IMG(src=self.get_url('static', 'required.png'))
        form = self.get_form(data['fields'],
                             data['href'],
                             values=data.get('values', dict()),
                             required=required,
                             legend=data['title'],
                             klass='input',
                             submit=self.submit)
        return DIV(P(form),
                   P(FORM(INPUT(type='submit', value='Cancel'),
                          method='GET',
                          action=data.get('cancel') or data['href'])))
