""" Adhoc web resource: simple bioinformatics tasks.

Base class for HTML representation of data.
"""

import urllib

import markdown
from HyperText.HTML40 import *

from wrapid.resource import *
from wrapid import html_utils

from . import configuration


class HtmlRepresentation(Representation):
    "HTML representation of the resource."

    mimetype = 'text/html'
    format = 'html'
    scripts = []

    def __call__(self, data):
        self.data = data
        try:
            refresh = data['refresh']
        except KeyError:
            head = self.get_head()
        else:
            url = "%s?refresh=%s" % (data['href'],
                                     min(configuration.MAX_REFRESH,
                                         configuration.REFRESH_FACTOR*refresh))
            head = self.get_head(META(http_equiv='Refresh',
                                      content="%s; url=%s" % (refresh, url)))
        html = HTML(head,
                    BODY(TABLE(TR(TD(TABLE(TR(TD(self.get_logo())),
                                           TR(TD(self.get_navigation()))),
                                     width='5%'),
                                  TD(H1(self.get_title()),
                                     DIV(self.get_description()),
                                     DIV(self.get_content())),
                                  TD(TABLE(TR(TD(self.get_login())),
                                           TR(TD(self.get_operations())),
                                           TR(TD(self.get_metadata())),
                                           TR(TD(self.get_outreprs()))))),
                               width='100%'),
                         HR(),
                         self.get_footer(),
                         self.get_scripts()))
        response = HTTP_OK(**self.get_http_headers())
        response.append(str(html))
        return response

    def get_url(self, *segments, **query):
        "Return a URL based on the application URL."
        url = '/'.join([self.data['application']['href']] + list(segments))
        if query:
            url += '?' + urllib.urlencode(query)
        return url

    def get_head(self, *elements):
        items = [TITLE(self.get_title()),
                 META(http_equiv='Content-Type',
                      content='text/html; charset=utf-8'),
                 META(http_equiv='Content-Script-Type',
                      content='application/javascript'),
                 LINK(rel='stylesheet',
                      href=self.get_url('static', 'style.css'),
                      type='text/css')]
        items.extend(elements)
        return HEAD(*items)

    def get_title(self):
        return self.data['title']

    def get_logo(self):
        return A(IMG(src=self.get_url('static', 'adhoc.png'),
                     width="100", height="96",
                     alt=self.data['application']['name'],
                     title=self.data['application']['name']),
                 href=self.data['application']['href'])

    def get_description(self):
        try:
            descr = self.data['descr']
        except KeyError:
            return ''
        else:
            return markdown.markdown(descr, output_format='html4')

    def get_content(self):
        return ''

    def get_operations(self):
        rows = []
        for operation in self.data.get('operations', []):
            method = operation.get('method', 'GET')
            jscode = None
            if method == 'DELETE':
                override = INPUT(type='hidden',
                                 name='http_method',
                                 value=method)
                method = 'POST'
                jscode = "return confirm('Delete cannot be undone; really delete?');"
            elif method == 'PUT':
                override = INPUT(type='hidden',
                                 name='http_method',
                                 value=method)
                method = 'POST'
            else:
                override = ''
            rows.append(TR(TD(FORM(INPUT(type='submit',
                                         value=operation['title'],
                                         onclick=jscode),
                                   override,
                                   method=method,
                                   action=operation['href']))))
        return TABLE(*rows)

    def get_metadata(self):
        return ''

    def get_login(self):
        loginname = self.data.get('loginname')
        if loginname:
            url = self.get_url('account', loginname)
            return DIV("Logged in as: %s" % A(loginname, href=url),
                       style='white-space: nowrap;')
        else:
            return I('not logged in',
                       style='white-space: nowrap;')

    def get_navigation(self):
        rows = []
        current = None
        items = []
        for link in self.data.get('links', []):
            title = link['title']
            try:
                family, name = title.split(':', 1)
            except ValueError:
                if items:
                    rows.append(TR(TD(family, UL(*items))))
                    items = []
                rows.append(TR(TD(A(title, href=link['href']))))
            else:
                items.append(LI(A(name, href=link['href'])))
        if items:
            rows.append(TR(TD(family, UL(*items))))
        return TABLE(klass='navigation', *rows)

    def get_outreprs(self):
        rows = []
        for link in self.data.get('outreprs', []):
            if link['title'] == 'HTML': continue # Skip itself
            rows.append(TR(TD(A(link['title'], href=link['href']))))
        return TABLE(klass='navigation', *rows)

    def get_footer(self):
        application = self.data['application']
        host = application['host']
        return TABLE(TR(TD("%(name)s %(version)s" % application,
                           style='width:33%;'),
                        TD(A(host.get('title') or host['href'],
                             href=host['href']),
                           style='width:33%; text-align:center;'),
                        TD("%(contact)s (%(email)s)" % host,
                           style='width:33%;text-align:right;')),
                     width='100%')

    def get_scripts(self):
        result = []
        for script in self.scripts:
            result.append(SCRIPT(type='text/javascript',
                                 src=self.get_url('static', script)))
        return DIV(*result)

    def get_form(self, funcs=dict(), submit='Save'):
        try:
            data = self.data['tool']
        except KeyError:
            data = self.data['form']
        form = html_utils.get_form(data['fields'],
                                   data['href'],
                                   funcs=funcs,
                                   values=data.get('values', dict()),
                                   required=IMG(src=self.get_url('static',
                                                                 'required.png')),
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
                       
