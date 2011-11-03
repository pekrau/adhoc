""" Adhoc web resource: simple bioinformatics tasks.

Task resources.
"""

import os
import uuid
import json

from wrapid.resource import *
from wrapid.fields import *
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration
from . import usage
from .method_mixin import *
from .html_representation import *


class GET_Tasks(GET_Mixin, GET):
    "Return the tasks list page."

    def __init__(self):
        super(GET_Tasks, self).__init__(
            outreprs=[JsonRepresentation(),
                      TextRepresentation(),
                      TasksHtmlRepresentation()],
            descr=self.__doc__)

    def is_access(self):
        if self.accountname:
            return self.is_admin() or self.accountname == self.login.name
        else:
            return self.is_admin()

    def add_data(self, data, resource, request, application):
        # Legacy issue: older account names may contain dot,
        # which screws up format handling.
        from .account import get_account_legacy
        account = get_account_legacy(self.cnx, resource.variables)
        if account:
            self.accountname = account.name
        else:
            if resource.variables.get('account'): # Account given, not found
                raise HTTP_NOT_FOUND
            self.accountname = None
        self.allow_access()
        data['entity'] = 'tasks'
        if self.accountname:
            data['title'] = "Tasks for account %s" % self.accountname
        else:
            data['title'] = 'Tasks'
        tasks = []
        for task in self.get_tasks(self.accountname):
            tasks.append(dict(iui=str(task.iui),
                              title=configuration.rstr(task.title),
                              account=task.account,
                              tool=str(task.tool),
                              status=str(task.status),
                              cpu_time=task.data.get('cpu_time'),
                              size=task.size,
                              modified=str(task.modified),
                              href=task.href))
        data['tasks'] = tasks

    def get_tasks(self, accountname=None):
        "Get all tasks; for the account name, if given."
        values = []
        sql = 'SELECT t.iui FROM task AS t'
        if accountname:
            sql += ', account AS a WHERE t.account=a.id AND a.name=?'
            values.append(accountname)
        sql += ' ORDER BY t.modified DESC'
        cursor = self.execute(sql, *values)
        result = []
        for record in cursor:
            result.append(Task(self.cnx, record[0]))
        return result


class TasksHtmlRepresentation(HtmlRepresentation):
    "HTML representation of the task list."

    scripts = ['jquery-1.6.4.min.js',
               'jquery.localtime-0.5.js']

    def get_content(self):
        rows = [TR(TH('Title'),
                   TH('Account'),
                   TH('Tool'),
                   TH('Status'),
                   TH('CPU time (s)'),
                   TH('Size (bytes)'),
                   TH('Modified'))]
        for task in self.data['tasks']:
            cpu_time = task['cpu_time']
            if cpu_time is None:
                cpu_time = '?'
            else:
                cpu_time = "%.2f" % cpu_time
            rows.append(TR(TD(A(task.get('title') or '[no title]',
                                href=task['href'])),
                           TD(task['account']),
                           TD(task['tool']),
                           TD(self.get_status(task['status'])),
                           TD(cpu_time, klass='number'),
                           TD(task['size'], klass='number'),
                           TD(task['modified'], klass='localtime')))
        return TABLE(klass='list', *rows)


class GET_Task(GET_Mixin, GET):
    "Return the task page."

    def __init__(self):
        super(GET_Task, self).__init__(
            infields=Fields(FloatField('refresh',
                                       descr='If the task has a dynamic status,'
                                       ' refresh the HTML page after the'
                                       ' specified number of seconds.')),
            outreprs=[TaskJsonRepresentation(),
                      TaskTextRepresentation(),
                      TaskHtmlRepresentation()],
            descr=self.__doc__)

    def is_access(self):
        return self.is_admin() or self.task.account == self.login.name

    def add_data(self, data, resource, request, application):
        self.task = Task(self.cnx, resource.variables['iui'])
        self.allow_access()
        data['entity'] = 'task'
        data['title'] = self.task.title or None
        data['task'] = configuration.rstr(self.task.get_data(resource.get_url))
        if not data['task'].has_key('cpu_time') and self.task.pid:
            try:
                process = usage.Usage(pid=self.task.pid,
                                      include_children=True)
            except ValueError:
                pass
            else:
                data['task']['cpu_time'] = process.cpu_time
        data['operations'] = [dict(title='Delete this task',
                                   href=resource.get_url(),
                                   method='DELETE')]
        if self.task.status in configuration.DYNAMIC_STATUSES:
            inputs = self.infields.parse(request)
            refresh = inputs.get('refresh')
            if refresh:
                data['refresh'] = min(configuration.MAX_REFRESH,
                                      max(1.0, refresh))
                

class TaskHtmlRepresentation(HtmlRepresentation):
    "HTML representation of the task data."

    scripts = ['jquery-1.6.4.min.js',
               'jquery.localtime-0.5.js']

    NONE = I('[none]')

    def get_title(self):
        return "%s task: %s" % (self.data['task']['tool'],
                                self.data['title'] or '[no title]')

    def get_content(self):
        taskdata = self.data['task']
        rows = []
        if taskdata['status']['value'] in configuration.DYNAMIC_STATUSES and \
           not self.data.has_key('refresh'):
            rows.append(TR(TH(),
                           TD(FORM(INPUT(type='submit',
                                         value='Auto-refresh this page'),
                                   INPUT(type='hidden',
                                         name='refresh', value='1.0'),
                                   method='GET',
                                   action=self.data['href']))))
        rows.append(TR(TH(A('Status',
                            href=taskdata['href'] + '/status')),
                       TD(self.get_status(taskdata['status']['value']))))
        rows.append(TR(TH('Modified'),
                       TD(taskdata['modified'], klass='localtime')))
        rows.append(TR(TH('Size (bytes)'),
                       TD(taskdata['size'])))
        cpu_time = taskdata.get('cpu_time')
        if cpu_time is None:
            cpu_time = '?'
        else:
            cpu_time = "%.2f" % cpu_time
        rows.append(TR(TH('CPU time (s)'), TD(cpu_time)))
        command = taskdata.get('command')
        if command:
            command = CODE(command)
        else:
            command = self.NONE
        rows.append(TR(TH('Command'), TD(command)))
        error = taskdata.get('error')
        if error:
            error = PRE(error)
        else:
            error = self.NONE
        rows.append(TR(TH('Error'), TD(error)))
        rows.append(self.get_data_item_row('output'))
        rows.append(self.get_data_item_row('query'))
        return TABLE(klass='output', *rows)

    def get_data_item_row(self, name):
        item = self.data['task'].get(name, dict())
        url = item.get('href')
        mimetype = item.get('mimetype')
        if mimetype == 'text/plain':
            content = item.get('content')
            if content:
                content = PRE(content)
            else:
                content = self.NONE
        else:
            size = item.get('size', 0)
            content = "%s (%s bytes)" % (mimetype, size)
            if url and size:
                content = A(content, href=url)
        if url:
            link = A(name.capitalize(), href=url)
        else:
            link = name.capitalize()
        return TR(TH(link), TD(content))


class TaskJsonRepresentation(JsonRepresentation):
    "JSON representation of the task data."

    def modify(self, data):
        "Get rid of some data that should not be shown in this representation."
        try: data['task']['query'].pop('content')
        except KeyError: pass
        try: data['task']['output'].pop('content')
        except KeyError: pass
        try: data['task'].pop('parameters')
        except KeyError: pass


class TaskTextRepresentation(TextRepresentation):
    "Text representation of the task data."

    def modify(self, data):
        "Get rid of some data that should not be shown in this representation."
        try: data['task']['query'].pop('content')
        except KeyError: pass
        try: data['task']['output'].pop('content')
        except KeyError: pass
        try: data['task'].pop('parameters')
        except KeyError: pass


class GET_TaskData(GET_Mixin, Method):
    "Return a data item for the task."

    def __init__(self, descr=None):
        super(GET_TaskData, self).__init__(descr=descr)

    def __call__(self, resource, request, application):
        self.connect(resource, request, application)
        try:
            self.task = Task(self.cnx, resource.variables['iui'])
            self.allow_access()
            return self.get_response()
        finally:
            self.close()

    def is_access(self):
        return self.is_admin() or self.task.account == self.login.name

    def get_response(self):
        raise NotImplementedError


class GET_TaskStatus(GET_TaskData):
    "Return the task status."

    def __init__(self):
        super(GET_TaskStatus, self).__init__(descr=self.__doc__)
        self.outreprs = [DummyRepresentation('text/plain',
                                             'The task status as text.')]

    def get_response(self):
        response = HTTP_OK(content_type='text/plain')
        try:
            response.append(str(self.task.status))
        except KeyError:
            raise HTTP_NOT_FOUND
        return response


class GET_TaskQuery(GET_TaskData):
    "Return the task query."

    def __init__(self):
        super(GET_TaskQuery, self).__init__(descr=self.__doc__)
        self.outreprs = [DummyRepresentation('*/*',
                                             'The task query, in its native mimetype.')]

    def get_response(self):
        mimetype = str(self.task.data.get('query_content_type',
                                          'text/plain'))
        response = HTTP_OK(content_type=mimetype)
        try:
            response.append(str(self.task.data['query']))
        except KeyError:
            raise HTTP_NOT_FOUND
        return response


class GET_TaskOutput(GET_TaskData):
    "Return the task output."

    def __init__(self):
        super(GET_TaskOutput, self).__init__(descr=self.__doc__)
        self.outreprs = [DummyRepresentation('*/*',
                                             'The task output, in its native mimetyp.')]

    def get_response(self):
        mimetype = str(self.task.data.get('output_content_type', 'text/plain'))
        response = HTTP_OK(content_type=mimetype)
        try:
            response.append(str(self.task.data['output']))
        except KeyError:
            raise HTTP_NOT_FOUND
        return response


class DELETE_Task(BaseMixin, DELETE):
    """Delete the task.
    The response is a HTTP 303 'See Other' redirection to the URL of the list
    of tasks for the account of this task.
    """

    def __call__(self, resource, request, application):
        self.connect(resource, request, application)
        try:
            self.task = Task(self.cnx, resource.variables['iui'])
            account = self.task.account
            self.allow_access()
            self.task.delete()
        finally:
            self.close()
        raise HTTP_SEE_OTHER(Location=application.get_url('tasks', account))

    def is_access(self):
        return self.is_admin() or self.task.account == self.login.name
        

            
class Task(object):
    "Task container and execution manager."

    def __init__(self, cnx, iui=None):
        self.cnx = cnx
        if iui is None:
            self.id = None
            self.iui = uuid.uuid4().hex
            self.href = None
            self.tool = None
            self.title = None
            self.status = configuration.CREATED
            self.pid = None
            self.size = None
            self.account = None
            self.modified = None
            self.data = dict()
        else:
            self.load(iui)

    def __str__(self):
        return "%s task: %s" % (self.tool, self.title or '[no title]')

    def get_data(self, urlfunc):
        result = self.data.copy()
        result['iui'] = self.iui
        result['href'] = self.href
        result['tool'] = self.tool
        result['size'] = self.size
        result['modified'] = self.modified
        result['status'] = dict(value=self.status,
                                href=urlfunc('status'))
        content = result.pop('query')
        query = dict(content=content,
                     size=len(content or ''),
                     # XXX fix this for the general case
                     ## mimetype=data['task'].pop('query_content_type'),
                     mimetype='text/plain',
                     href=urlfunc('query'))
        result['query'] = query
        content = result.pop('output', None)
        if content is not None:
            output = dict(content=content,
                          size=len(content),
                          mimetype=result.pop('output_content_type'),
                          href=urlfunc('output'))
            result['output'] = output
        return result

    def execute(self, sql, *values):
        cursor = self.cnx.cursor()
        cursor.execute(sql, values)
        return cursor

    def load(self, iui):
        self.iui = iui
        cursor = self.execute('SELECT t.id,t.href,t.tool,t.title,t.status,'
                              ' t.pid,t.size,a.name,t.modified'
                              ' FROM task AS t, account AS a'
                              ' WHERE iui=? and t.account=a.id', self.iui)
        record = cursor.fetchone()
        if not record:
            raise ValueError("no such task %s" % self.iui)
        self.id = record[0]
        self.href = str(record[1])
        self.tool = str(record[2])
        self.title = configuration.rstr(record[3])
        self.status = str(record[4])
        self.pid = record[5]
        self.size = record[6]
        self.account = str(record[7])
        self.modified = str(record[8])
        infile = open(os.path.join(configuration.TASK_DIR, self.iui))
        self.data = json.load(infile)
        infile.close()

    def create(self, accountid):
        assert self.iui
        assert self.id is None
        self.accountid = accountid
        self.modified = configuration.now()
        cursor = self.execute('INSERT INTO task(iui,href,tool,title,status,'
                              'pid,account,modified) VALUES(?,?,?,?,?,?,?,?)',
                              self.iui,
                              self.href,
                              self.tool,
                              self.title,
                              self.status,
                              self.pid,
                              self.accountid,
                              self.modified)
        self.id = cursor.lastrowid
        self._update()

    def save(self):
        assert self.iui
        assert self.id
        self.execute('UPDATE task SET title=?, status=? WHERE id=?',
                     self.title,
                     self.status,
                     self.id)
        self._update()

    def set_pid(self, new):
        self.pid = new
        self.execute('UPDATE task SET pid=?, modified=? WHERE iui=?',
                     new,
                     configuration.now(),
                     self.iui)
        self.cnx.commit()

    def set_status(self, new):
        self.status = new
        self.execute('UPDATE task SET status=?, modified=? WHERE iui=?',
                     new,
                     configuration.now(),
                     self.iui)
        self.cnx.commit()

    def _update(self):
        assert self.iui
        assert self.id
        filename = os.path.join(configuration.TASK_DIR, self.iui)
        outfile = open(filename, 'w')
        json.dump(self.data, outfile)
        outfile.close()
        self.size = os.path.getsize(filename)
        self.modified = configuration.now()
        self.execute('UPDATE task SET size=?, modified=? WHERE id=?',
                     self.size,
                     self.modified,
                     self.id)
        self.cnx.commit()

    def delete(self):
        assert self.iui
        assert self.id
        if self.status == configuration.EXECUTING:
            os.kill(self.pid, signal.SIGKILL)
        self.execute('DELETE FROM task WHERE id=?', self.id)
        self.cnx.commit()
        os.remove(os.path.join(configuration.TASK_DIR, self.iui))
        try:
            os.remove(os.path.join(configuration.TASK_DIR, "%s.out"%self.iui))
        except OSError:
            pass
        try:
            os.remove(os.path.join(configuration.TASK_DIR, "%s.err"%self.iui))
        except OSError:
            pass
