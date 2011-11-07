""" Adhoc web resource: simple bioinformatics tasks.

Base class for HTML representation of data.
"""

import urllib

from wrapid.resource import *
from wrapid.html_representation import *

from . import configuration


class HtmlRepresentation(BaseHtmlRepresentation):
    "HTML representation of the resource."

    def get_url(self, *segments, **query):
        "Return a URL based on the application URL."
        url = '/'.join([self.data['application']['href']] + list(segments))
        if query:
            url += '?' + urllib.urlencode(query)
        return url

    def get_head(self):
        head = super(HtmlRepresentation, self).get_head()
        head.append(LINK(rel='stylesheet',
                         href=self.get_url('static', 'style.css'),
                         type='text/css'))
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

    def get_logo(self):
        return A(IMG(src=self.get_url('static', 'adhoc.png'),
                     width="100", height="96",
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

    def get_form_panel(self, funcs=dict(), submit='Save'):
        try:
            data = self.data['tool']
        except KeyError:
            data = self.data['form']
        required = IMG(src=self.get_url('static', 'required.png'))
        form = self.get_form(data['fields'],
                             data['href'],
                             funcs=funcs,
                             values=data.get('values', dict()),
                             required=required,
                             legend=data['title'],
                             klass='input',
                             submit=submit)
        return DIV(P(form),
                   P(FORM(INPUT(type='submit', value='Cancel'),
                          method='GET',
                          action=data.get('cancel') or data['href'])))

    def get_status(self, status):
        if status not in configuration.STATUSES:
            raise ValueError("invalid status '%s'" % status)
        return self.get_icon(status, label=status)

    def get_icon(self, icon, label=None):
        items = [IMG(src=self.get_url('static', "%s.png" % icon),
                     alt=label or icon, title=label or icon, klass='icon')]
        if label:
            items.append(SPAN(" %s" % label, klass='icon'))
        return DIV(*items)
