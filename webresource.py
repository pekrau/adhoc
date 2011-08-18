""" Adhoc web resource.

WebResource: Base HTTP request dispatcher class.
"""

import logging
import mimetypes
import sqlite3
import json
import urlparse
import httplib

from wireframe.response import *
from wireframe import basic_authenticate
from wireframe.dispatcher import BaseDispatcher

from . import configuration
from . import mimeutils
from .html_representation import *


class WebResource(BaseDispatcher):
    "WebResource: Base HTTP request dispatcher class."

    def prepare(self, request, response):
        """Prepare for request processing:
        1) Get the database connection.
        2) Authenticate user account and get information.
        3) Get user agent information.
        4) Get the explicit accept types for content negotiation.
        """
        self.request = request
        self.cnx = sqlite3.connect(configuration.ADHOC_FILE)
        self.user = self.get_user()
        self.user_agent = request.environ.get('HTTP_USER_AGENT')
        self.accept = set()
        for item in request.headers.get('Accept', 'text/html').split(','):
            self.accept.add(item.strip().split(';')[0].strip())

    def get_user(self):
        "Get the data for authenticated user account."
        try:
            name, password = basic_authenticate.decode(self.request)
            cursor = self.execute('SELECT id,password,teams,email,preferences,'
                                  ' description FROM account WHERE name=?',
                                  name)
            record = cursor.fetchone()
            if not record: raise ValueError
            if record[1] != configuration.get_password_hexdigest(password):
                raise ValueError
        except ValueError:
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm='adhoc')
        preferences = record[4]
        if preferences:
            preferences = json.loads(preferences)
        else:
            preferences = dict()
        return dict(id=record[0],
                    name=name,
                    password=record[1],
                    teams=set(record[2].split()),
                    email=record[3],
                    preferences=preferences,
                    description=record[5])

    def update_user_preferences(self, tool, preferences):
        self.user['preferences'][tool] = preferences
        self.execute('UPDATE account SET preferences=? WHERE name=?',
                     json.dumps(self.user['preferences']),
                     self.user['name'])
        self.commit()

    def is_admin(self):
        "Is user admin?"
        return 'admin' in self.user['teams']

    def check_admin(self):
        "Raise HTTP FORBIDDEN if user is not admin."
        if not self.is_admin():
            raise HTTP_FORBIDDEN("'admin' account required for this resource")

    def check_read(self): 
        "Raise HTTP FORBIDDEN if user does not have read privilege."
        pass

    def check_write(self):
        "Raise HTTP FORBIDDEN if user does not have write privilege."
        pass

    def get_cgi_value(self, name, required=False, cleanup=True):
        "Get the single value from the request CGI data."
        try:
            value = self.request.cgi_fields[name].value.strip()
            if cleanup:
                value = value.replace('\r\n', '\n').strip()
                value = unicode(value)
            if not value: raise KeyError
        except KeyError:
            if required:
                raise HTTP_BAD_REQUEST("no '%s' value" % name)
            else:
                return None
        else:
            return value

    def get_cgi_file_content(self, name):
        "Return the content of the named file field. None if no such file."
        try:
            infile = self.request.cgi_fields[name].file
            if not infile: raise KeyError
            return infile.read()
        except KeyError:
            return None

    def get_url_content(self, url):
        "Return the content of the given HTTP URLs."
        try:
            parts = urlparse.urlsplit(url)
            if parts.scheme != 'http':
                raise ValueError('not HTTP')
            if not parts.netloc:
                raise ValueError('invalid URL')
            cnx = httplib.HTTPConnection(parts.netloc,
                                         parts.port or 80,
                                         timeout=configuration.HTTP_TIMEOUT)
            cnx.request('GET', parts.path)
            response = cnx.getresponse()
            if response.status != 200:
                raise ValueError("response %s %s" %
                                 (response.status, response.reason))
            content = response.read()
            if not content:
                raise ValueError('no content')
            return content
        except Exception, msg:
            raise HTTP_BAD_REQUEST("%s : URL %s" % (msg, url))

    def execute(self, sql, *values):
        cursor = self.cnx.cursor()
        cursor.execute(sql, values)
        return cursor

    def commit(self):
        self.cnx.commit()


class Static(WebResource):
    "Return a static file."

    def GET(self, request, response):
        "Return the static file with the mimetype derived from its format."
        filename = request.path_named_values['filename']
        try:
            with open(configuration.get_static_path(filename)) as infile:
                data = infile.read()
        except (ValueError, IOError):
            raise HTTP_NOT_FOUND
        mimetype = mimetypes.guess_type(filename)
        if mimetype:
            response['Content-Type'] = mimetype
        response.append(data)


class Tasks(WebResource):
    "Tasks list."

    def GET(self, request, response):
        from .task import get_tasks
        self.check_admin()
        accounts = dict()
        for record in self.execute('SELECT id, name FROM account'):
            accounts[record[0]] = record[1]
        html = HtmlRepresentation(self, 'Tasks')
        rows = [TR(TH('Task'),
                   TH('Account'),
                   TH('Tool'),
                   TH('Status'),
                   TH('CPU time'),
                   TH('Size'),
                   TH('Modified'))]
        for task in get_tasks(self.cnx):
            url = configuration.get_url('account', accounts[task.account])
            cpu_time = task.data.get('cpu_time')
            if cpu_time is None:
                cpu_time = NONE
            else:
                cpu_time = "%.2f" % cpu_time
            rows.append(TR(TD(A(task.title or I('[untitled]'),
                                href=task.get_url())),
                           TD(A(accounts[task.account], href=url)),
                           TD(task.tool),
                           TD(html.get_status(task.status)),
                           TD(cpu_time, klass='number'),
                           TD(task.size, klass='number'),
                           TD(task.modified)))
        if len(rows) <= 1:
            rows.append(TR(TD(NONE)))
        html.append(TABLE(klass='list', *rows))
        html.write(response)


class AccountTasks(WebResource):
    "Tasks list for an account."

    def prepare(self, request, response):
        super(AccountTasks, self).prepare(request, response)
        self.accountname = request.path_named_values['account']
        cursor = self.execute('SELECT id FROM account WHERE name=?',
                              self.accountname)
        record = cursor.fetchone()
        if not record:
            raise HTTP_NOT_FOUND
        self.account = record[0]

    def check_read(self):
        if self.is_admin(): return
        if self.user['name'] == self.accountname: return
        raise HTTP_FORBIDDEN

    def GET(self, request, response):
        from .task import get_tasks
        self.check_read()
        html = HtmlRepresentation(self,
                                  "Tasks for account %s" % self.accountname)
        rows = [TR(TH('Task'),
                   TH('Tool'),
                   TH('Status'),
                   TH('CPU time'),
                   TH('Size'),
                   TH('Modified'))]
        for task in get_tasks(self.cnx, self.account):
            cpu_time = task.data.get('cpu_time')
            if cpu_time is None:
                cpu_time = NONE
            else:
                cpu_time = "%.2f" % cpu_time
            rows.append(TR(TD(A(task.title or I('[untitled]'),
                                href=task.get_url())),
                           TD(task.tool),
                           TD(html.get_status(task.status)),
                           TD(cpu_time, klass='number'),
                           TD(task.size, klass='number'),
                           TD(task.modified)))
        if len(rows) <= 1:
            rows.append(TR(TD(NONE)))
        html.append(TABLE(klass='list', *rows))
        html.write(response)


class TaskResource(WebResource):

    MAX_REFRESH = 60.0

    def prepare(self, request, response):
        from .task import Task
        super(TaskResource, self).prepare(request, response)
        try:
            iui = request.path_named_values['iui']
        except KeyError:
            raise HTTP_NOT_FOUND
        try:
            self.task = Task(self.cnx, iui)
        except ValueError:
            raise HTTP_NOT_FOUND

    def set_refresh(self, request, response):
        if self.task.status != 'executing': return
        refresh = self.get_cgi_value('refresh')
        if refresh:
            try:
                refresh = min(self.MAX_REFRESH, float(refresh))
            except ValueError:
                refresh = 1.0
        else:
            refresh = 1.0
        url = self.task.get_url(refresh=str(min(self.MAX_REFRESH, 2*refresh)))
        response['Refresh'] = "%s; url=%s" % (refresh, url)

    def add_delete(self, html):
        jscode = "return confirm('Delete cannot be undone; really delete?');"
        html.operations.append(FORM(INPUT(type='submit', value='Delete',
                                          onclick=jscode),
                                    INPUT(type='hidden',
                                          name='http_method', value='DELETE'),
                                    method='POST',
                                    action=self.task.get_url()))

    def DELETE(self, request, response):
        self.task.delete()
        raise HTTP_SEE_OTHER(Location=configuration.get_url('tasks',
                                                            self.user['name']))


class TaskDisplay(TaskResource):
    "Display the current state of a task."

    def GET(self, request, response):
        html = HtmlRepresentation(self, str(self.task))
        self.add_delete(html)
        rows = [TR(TH('Status'),
                   TD(html.get_status(self.task.status))),
                TR(TH('Modified'),
                   TD(self.task.modified)),
                TR(TH('Size'),
                   TD(self.task.size)),
                TR(TH('CPU time'),
                   TD(str(self.task.data.get('cpu_time', NONE)))),
                TR(TH('Command'),
                   TD(CODE(self.task.data.get('command') or NONE))),
                TR(TH('Error'),
                   TD(PRE(self.task.data.get('error') or NONE)))]
        content_type = self.task.data.get('output_content_type')
        output = self.task.data.get('output')
        if content_type == 'text/plain':
            rows.append(TR(TH(A('Output', href=self.task.get_url('output'))),
                           TD(PRE(output or NONE))))
        elif content_type:
            rows.append(TR(TH(A('Output', href=self.task.get_url('output'))),
                           TD("%s (%s bytes)" % (content_type,
                                                 len(output or '')))))
        else:
            rows.append(TR(TH('Output'),
                           TD(NONE)))
        rows.append(TR(TH('Query'),
                       TD(PRE(self.task.data.get('query') or NONE))))
        html.append(P(TABLE(klass='output', *rows)))
        self.set_refresh(request, response)
        html.write(response)


class TaskStatus(TaskResource):
    "Return the status of the task as text."

    def GET(self, request, response):
        response['Content-Type'] = 'text/plain'
        response.append(self.task.status)


class TaskOutput(TaskResource):
    "Return the output of the task as a file."

    def GET(self, request, response):
        if self.task.status != 'finished':
            raise HTTP_NOT_FOUND
        mimetype = self.task.data['output_content_type']
        response['Content-Type'] = mimetype
        filename = self.task.title or 'output'
        filename += mimeutils.guess_extension(mimetype)
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        response.append(self.task.data['output'])
