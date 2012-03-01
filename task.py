""" Adhoc: Simple web application for task execution.

Task resources.
"""

from .method_mixin import *
from .representation import *


class TasksHtmlRepresentation(HtmlRepresentation):
    "HTML representation of the task list."

    def get_content(self):
        rows = [TR(TH('Title'),
                   TH('Status'),
                   TH('Tool'),
                   TH('CPU time (s)'),
                   TH('Size (bytes)'),
                   TH('Account'),
                   TH('Modified'))]
        for taskdata in self.data['tasks']:
            rows.append(TR(TD(A(taskdata.get('title') or '[no title]',
                                href=taskdata['href'])),
                           TD(self.get_icon(taskdata['status']['value'])),
                           TD(taskdata['tool']),
                           TD("%.1f" % taskdata['cpu_time'], klass='integer'),
                           TD(taskdata['size'], klass='integer'),
                           TD(taskdata['account']),
                           TD(taskdata['modified'], klass='localtime')))
        return TABLE(klass='list', *rows)


class GET_Tasks(MethodMixin, GET):
    "Display list of tasks."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                TasksHtmlRepresentation]

    def is_accessible(self):
        # XXX when filtered by access is implemented, then allow anyone
        return self.is_login_admin()

    def get_data_resource(self, resource, request, application):
        data = dict(title='Tasks',
                    resource='Task list',
                    tasks=[])
        # XXX need to be filtered by login access; see above
        for task in self.db.get_tasks():
            data['tasks'].append(task.get_data(application=application,
                                               full=False))
        return data


class GET_TasksAccount(MethodMixin, GET):
    "Display list of tasks for an account."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                TasksHtmlRepresentation]

    def set_current(self, resource, request, application):
        self.set_current_account(resource, request, application)

    def is_accessible(self):
        if self.is_login_admin(): return True
        if self.account['name'] == self.login['name']: return True
        if self.account['name'] == 'anonymous': return True
        return False

    def get_data_resource(self, resource, request, application):
        data = dict(title="Tasks for %s" % self.account['name'],
                    resource='Task list account',
                    tasks=[])
        for task in self.db.get_tasks(self.account['name']):
            data['tasks'].append(task.get_data(application=application,
                                               full=False))
        return data


class TaskHtmlRepresentation(HtmlRepresentation):
    "HTML representation of the task data."

    NONE = I('[none]')

    def get_title(self):
        return "%s task: %s" % (self.data['task']['tool'],
                                self.data['title'] or '[no title]')

    def get_content(self):
        taskdata = self.data['task']
        rows = []
        ## if taskdata['status']['value'] in configuration.DYNAMIC_STATUSES and \
        ##    not self.data.has_key('refresh'):
        ##     rows.append(TR(TH(),
        ##                    TD(FORM(INPUT(type='submit',
        ##                                  value='Auto-refresh this page'),
        ##                            INPUT(type='hidden',
        ##                                  name='refresh', value='1.0'),
        ##                            method='GET',
        ##                            action=self.data['href']))))
        status = taskdata['status']
        rows.append(TR(TH(A('Status', href=status['href'])),
                       TD(self.get_icon_labelled(status['value']))))
        rows.append(TR(TH('Modified'),
                       TD(taskdata['modified'], klass='localtime')))
        rows.append(TR(TH('CPU time (s)'), TD("%.1f" % taskdata['cpu_time'])))
        rows.append(TR(TH('Size (bytes)'),
                       TD(taskdata['size'])))
        command = taskdata.get('command')
        if command:
            command = CODE(command)
        else:
            command = self.NONE
        rows.append(TR(TH('Command'), TD(command)))
        error = taskdata.get('error')
        if error:
            error = PRE(self.safe_text(error))
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
                content = PRE(self.safe_text(content))
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


class TaskMixin(object):

    def set_current(self, resource, request, application):
        try:
            self.task = Task(self.db, iui=resource.variables['iui'])
        except KeyError:
            raise HTTP_NOT_FOUND

    def is_accessible(self):
        if self.is_login_admin(): return True
        if self.task.account == self.login['name']: return True
        return False


class GET_Task(TaskMixin, MethodMixin, GET):
    "Display the task."

    outreprs = [TaskJsonRepresentation,
                TaskTextRepresentation,
                TaskHtmlRepresentation]

    fields = (FloatField('refresh',
                         descr='If the task has a dynamic status,'
                         ' refresh the HTML page after the'
                         ' specified number of seconds.'),)

    def get_data_operations(self, resource, request, application):
        "Return the operations response data."
        return [dict(title='Delete',
                     href=resource.get_url(),
                     method='DELETE')]

    def get_data_resource(self, resource, request, application):
        "Return the dictionary with the resource-specific response data."
        data = dict(resource='Task',
                    title=self.task.title or None,
                    task=self.task.get_data(application=application))
        if self.task.status in configuration.DYNAMIC_STATUSES:
            inputs = self.parse_fields(request)
            refresh = inputs.get('refresh')
            if refresh:
                data['refresh'] = min(configuration.MAX_REFRESH,
                                      max(1.0, refresh))
            else:
                data['refresh'] = 1.0
        return data
                

class GET_TaskStatus(TaskMixin, MethodMixin, GET):
    "Return the task status."

    outreprs = [TextRepresentation]

    def get_response(self, resource, request, application):
        response = HTTP_OK(content_type='text/plain')
        try:
            response.append(str(self.task.status))
        except KeyError:
            raise HTTP_NOT_FOUND
        return response


class AnyDummyRepresentation(Representation):
    "The task query in its native mimetype."
    mimetype = '*/*'


class GET_TaskQuery(TaskMixin, MethodMixin, GET):
    "Return the task query."

    outrepresentations = (AnyDummyRepresentation,)

    def get_response(self, resource, request, application):
        mimetype = str(self.task.data.get('query_content_type', 'text/plain'))
        response = HTTP_OK(content_type=mimetype)
        try:
            response.append(str(self.task.data['query']))
        except KeyError:
            raise HTTP_NOT_FOUND
        return response


class GET_TaskOutput(TaskMixin, MethodMixin, GET):
    "Return the task output."

    outrepresentations = (AnyDummyRepresentation,)

    def get_response(self, resource, request, application):
        mimetype = str(self.task.data.get('output_content_type', 'text/plain'))
        response = HTTP_OK(content_type=mimetype)
        try:
            response.append(str(self.task.data['output']))
        except KeyError:
            raise HTTP_NOT_FOUND
        return response


class DELETE_Task(TaskMixin, MethodMixin, RedirectMixin, DELETE):
    "Delete the task."

    def handle(self, resource, request, application):
        self.redirect = application.get_url('tasks', self.task.account)
        self.task.delete()
