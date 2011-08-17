""" Adhoc web resource.

Basic HTML representation template.
"""

import markdown
from HyperText.HTML40 import *

from . import configuration

REQUIRED = IMG(src=configuration.get_url('static', 'required.png'))
NONE = I('[none]')

STATUS_ICONS = \
    dict(created=IMG(src=configuration.get_url('static', 'created.png'),
                     klass='status_icon'),
         waiting=IMG(src=configuration.get_url('static', 'waiting.png'),
                     klass='status_icon'),
         executing=IMG(src=configuration.get_url('static', 'executing.png'),
                       klass='status_icon'),
         finished=IMG(src=configuration.get_url('static', 'finished.png'),
                      klass='status_icon'),
         failed=IMG(src=configuration.get_url('static', 'failed.png'),
                    klass='status_icon'))



class HtmlRepresentation(object):
    "Basic HTML representation template."

    def __init__(self, webresource, title):
        self.webresource = webresource
        self.title = title
        self.set_logo()
        self.set_login()
        self.set_header()
        self.set_search()
        self.set_help()
        self.set_navigation()
        self.set_metadata()
        self.set_footer()
        self.abstract = ''
        self.content = []
        self.operations = []

    def append(self, element):
        self.content.append(element)

    def append_markdown(self, text):
        self.append(markdown.markdown(text, output_format='html4'))

    def add_operation(self, label, *trailing):
        self.operations.append(FORM(INPUT(type='submit', value=label),
                                    method='GET',
                                    action=configuration.get_url(*trailing)))

    def set_logo(self):
        self.logo = A(IMG(src=configuration.get_url('static', 'dna.png'),
                          width="100", height="96",
                          alt="adhoc %s" % configuration.VERSION),
                      href=configuration.URL_BASE)

    def set_header(self):
        self.header = H1(self.title)

    def set_login(self):
        url = configuration.get_url('account', self.webresource.user['name'])
        self.login = "Login: %s" % A(self.webresource.user['name'], href=url)
        # This is a non-standard way of achieving a logout in several
        # different browsers, which should include Firefox, Opera and
        # Safari, but not Internet Explorer.
        if self.webresource.user_agent:
            user_agent = self.webresource.user_agent.lower()
            for signature in ['firefox', 'opera', 'safari']:
                if signature in user_agent:
                    url = "http://logout:byebye@%s/" % configuration.URL_ROOT
                    self.login = TABLE(TR(TD(self.login),
                                          TD(FORM(INPUT(type='submit',
                                                        value='Logout'),
                                                  method='GET',
                                                  action=url))))

    def set_search(self):
        self.search = ''

    def set_help(self):
        self.help = ''

    def set_navigation(self):
        rows = []
        if self.webresource.is_admin():
            url = configuration.get_url('tasks')
            rows.append(TR(TD(A('Tasks', href=url))))
        url = configuration.get_url('tasks', self.webresource.user['name'])
        rows.append(TR(TD(A('My tasks', href=url))))
        if self.webresource.is_admin():
            url = configuration.get_url('accounts')
            rows.append(TR(TD(A('Accounts', href=url))))
        url = configuration.get_url('account', self.webresource.user['name'])
        rows.append(TR(TD(A('My account', href=url))))
        for tool in configuration.TOOLS:
            url = configuration.get_url(tool['name'])
            rows.append(TR(TD(A(tool['name'], href=url))))
        self.navigation = TABLE(klass='navigation', *rows)

    def set_metadata(self):
        self.metadata = []

    def set_footer(self):
        self.footer = TABLE(TR(TD("adhoc %s" % configuration.VERSION,
                                  style='width:33%;'),
                               TD(A('SciLifeLab',
                                    href='http://www.scilifelab.se/'),
                                  style='width:33%; text-align:center;'),
                               TD("Per Kraulis (%s)" %
                                  A('per.kraulis@scilifelab.se',
                                    href='mailto:per.kraulis@scilifelab.se'),
                                  style='width:34%;text-align:right;')),
                            width='100%')

    def write(self, response):
        "Write the HTML response output."
        response['Content-Type'] = 'text/html'
        response.append(str(HTML(self.get_head(), self.get_body())))

    def get_head(self):
        return HEAD(TITLE(self.title),
                    META(content='text/html; charset=utf-8',
                         http_equiv='Content-Type'),
                    META(content='application/javascript',
                         http_equiv='Content-Script-Type'),
                    LINK(rel='stylesheet',
                         href=configuration.get_url('static', 'style.css'),
                         type='text/css'))

    def get_body(self):
        return BODY(TABLE(TR(TH(self.logo, width='5%'),
                             TD(self.header,
                                self.abstract),
                             TD(TABLE(TR(TD(self.login)),
                                      TR(TD(self.search)),
                                      TR(TD(self.help))))),
                          TR(TD(self.navigation),
                             TD(*self.content),
                             TD(TABLE(TR(TD(*self.operations)),
                                      TR(TD(style='height: 1em;')),
                                      TR(TD(*self.metadata)),
                                      width='100%'))),
                          TR(TD(HR(), colspan=3)),
                          TR(TD(self.footer, colspan=3)),
                          klass='body',
                          width='100%'))

    def get_status(self, status):
        try:
            return DIV(STATUS_ICONS[status], status)
        except KeyError:
            return status
