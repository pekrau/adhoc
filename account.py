""" Adhoc web resource: simple bioinformatics tasks.

Account resources.
"""

import logging
import json
import string

from wrapid.resource import *
from wrapid.fields import *
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration
from .method_mixin import *
from .html_representation import *


class Account(object):
    "Container for account data."

    def __init__(self, cnx, name):
        self.name = configuration.rstr(name)
        cursor = cnx.cursor()
        cursor.execute('SELECT id,password,teams,max_tasks,email,description,'
                       'preferences FROM account WHERE name=?',
                       (name,))
        record = cursor.fetchone()
        if not record: raise ValueError
        self.id = record[0]
        self.password = record[1]
        self.teams = set(map(str, record[2].split()))
        self.max_tasks = record[3]
        self.email = configuration.rstr(record[4])
        self.description = configuration.rstr(record[5])
        preferences = record[6]
        if preferences:
            self.preferences = configuration.rstr(json.loads(preferences))
        else:
            self.preferences = dict()

    def check_password(self, password):
        if self.password != configuration.get_password_hexdigest(password):
            raise ValueError

    def get_data(self):
        "Return the account data in a dictionary."
        return dict(name=self.name,
                    teams=' '.join(self.teams),
                    max_tasks=self.max_tasks,
                    email=self.email,
                    preferences=self.preferences,
                    descr=self.description)


class GET_Accounts(GET_Mixin, GET):
    "Produce the accounts list."

    def __init__(self):
        super(GET_Accounts, self).__init__(
            outreprs=[JsonRepresentation(),
                      TextRepresentation(),
                      AccountsHtmlRepresentation()],
            descr=self.__doc__)

    def is_access(self):
        return self.is_admin()

    def add_data(self, data, resource, request, application):
        self.allow_admin()
        data['entity'] = 'accounts'
        data['title'] = 'Accounts'
        data['accounts'] = []
        cursor = self.execute('SELECT name FROM account ORDER BY name')
        for name in [r[0] for r in cursor.fetchall()]:
            account = Account(self.cnx, name).get_data()
            account['href'] = application.get_url('account', name)
            count, size = self.get_tasks_stats(name)
            account['tasks'] = dict(href=application.get_url('tasks', name),
                                    total_count=count,
                                    total_size=size)
            data['accounts'].append(account)
        data['operations'] = [dict(title='Create account',
                                   href=application.get_url('account'))]


class AccountsHtmlRepresentation(HtmlRepresentation):
    "HTML representation of the accounts list."

    def get_content(self):
        rows = [TR(TH('Name'),
                   TH('Teams'),
                   TH('# tasks'),
                   TH('Max # tasks'),
                   TH('Total task size'),
                   TH('Email'))]
        for account in self.data['accounts']:
            max_tasks = account.get('max_tasks', -1)
            error = ''
            if max_tasks >= 0:
                if account['tasks']['total_count'] >= max_tasks:
                    error = self.get_icon('error', 'Max number reached!')
            rows.append(TR(TD(A(account['name'], href=account['href'])),
                           TD(account['teams']),
                           TD(A(str(account['tasks']['total_count']),
                                href=account['tasks']['href']),
                              error,
                              klass='number'),
                           TD(account['max_tasks'], klass='number'),
                           TD(str(account['tasks']['total_size']),
                              klass='number'),
                           TD(account.get('email') or '')))
        return TABLE(klass='list', *rows)


class GET_Account(GET_Mixin, GET):
    "Produce the account data."

    def __init__(self):
        super(GET_Account, self).__init__(
            outreprs=[JsonRepresentation(),
                      TextRepresentation(),
                      AccountHtmlRepresentation()],
            descr=self.__doc__)

    def is_access(self):
        return self.is_admin() or self.login.name == self.account.name

    def add_data(self, data, resource, request, application):
        self.account = self.get_account(resource.variables)
        if not self.account:
            raise HTTP_NOT_FOUND
        self.allow_access()
        data['entity'] = 'account'
        data['title'] = "Account %s" % self.account.name
        data['account'] = self.account.get_data()
        count, size = self.get_tasks_stats(self.account.name)
        data['account']['tasks'] = dict(
            href=application.get_url('tasks', self.account.name),
            total_count=count,
            total_size=size)
        if self.login.name != 'anonymous':
            data['operations'] = [
                dict(title='Edit account',
                     href=application.get_url('account',
                                              self.account.name,'edit'))]


class AccountHtmlRepresentation(HtmlRepresentation):
    "HTML representation of the account data."

    def get_content(self):
        account = self.data['account']
        table = TABLE(klass='input')
        # Teams can be edited only when user is admin
        try:
            table.append(TR(TH('Teams'),
                            TD(account['teams'])))
        except KeyError:
            pass
        line = str(A(str(account['tasks']['total_count']),
                     href=account['tasks']['href']))
        max_tasks = account.get('max_tasks', -1)
        if max_tasks >= 0:
            if account['tasks']['total_count'] >= max_tasks:
                line += " %s" % self.get_icon('error', 'Max number reached!')
        table.append(TR(TH('# tasks'),
                        TD(line)))
        # Max number of tasks can be edited only when user is admin
        try:
            table.append(TR(TH('Max # tasks'),
                            TD(account['max_tasks'])))
        except KeyError:
            pass
        table.append(TR(TH('Total tasks size'),
                        TD(str(account['tasks']['total_size']))))
        table.append(TR(TH('Email'),
                        TD(account.get('email') or '')))
        table.append(TR(TH('Description'),
                        TD(markdown_to_html(account.get('descr')))))
        return table


CREATE_FIELDS = Fields(StringField('name', title='Name',
                                   required=True,
                                   descr='Account name, which must be unique.'
                                   ' May contain alphanumerical characters,'
                                   ' dash (-), underscore (_) and dot (.)'),
                       PasswordField('password', title='Password',
                                     required=True,
                                     descr='At least 6 characters.'),
                       PasswordField('confirm_password',
                                     title='Confirm password',
                                     required=True),
                       MultiSelectField('teams', title='Teams',
                                        required=True, check=False),
                       IntegerField('max_tasks', title='Max number of tasks',
                                    required=True,
                                    default=configuration.DEFAULT_MAX_TASKS,
                                    descr='Maximum number of stored tasks.'
                                    ' Use -1 to denote no limit.'),
                       StringField('email', title='Email'),
                       TextField('descr', title='Description'))


class GET_AccountCreate(GET_Mixin, GET):
    "Produce the create form for a new account."

    def __init__(self):
        super(GET_AccountCreate, self).__init__(
            outreprs=[JsonRepresentation(),
                      TextRepresentation(),
                      AccountCreateHtmlRepresentation()],
            descr=self.__doc__)

    def is_access(self):
        return self.is_admin()

    def add_data(self, data, resource, request, application):
        data['title'] = 'Create account'
        fill = dict(teams=dict(options=configuration.get_teams()))
        data['form'] = dict(fields=CREATE_FIELDS.get_data(fill=fill),
                            title='Enter data for new account',
                            href=resource.get_url(),
                            cancel=application.get_url('accounts'))
        

class POST_AccountCreate(POST_Mixin, POST):
    """Perform the account creation. The response consists of a
    HTTP 303 'See Other' redirection to the URL /account{account}.
    There is no output representation for this resource and method.
    """

    def __init__(self):
        super(POST_AccountCreate, self).__init__(infields=CREATE_FIELDS,
                                                 descr=self.__doc__)

    def is_access(self):
        return self.is_admin()

    def action(self, resource, request, application):
        "Handle the request and return a response instance."
        self.allow_access()
        inserts = self.infields.parse(request)
        inserts['name'] = inserts['name'].strip()
        if len(inserts['name']) <= 3:
            raise HTTP_BAD_REQUEST('account name is too short')
        allowed = string.letters + string.digits + '-_.'
        if set(inserts['name']).difference(allowed):
            raise HTTP_BAD_REQUEST('account name contains disallowed characters')
        cursor = self.execute('SELECT COUNT(*) FROM account WHERE name=?',
                              inserts['name'])
        if cursor.fetchone()[0] != 0:
            raise HTTP_BAD_REQUEST("account name '%s' already in use" %
                                   inserts['name'])
        if len(inserts['password']) < 6:
            raise HTTP_BAD_REQUEST('password must contain at least 6 characters')
        if inserts['password'] != inserts.pop('confirm_password'):
                raise HTTP_BAD_REQUEST('passwords not equal')
        inserts['password'] = configuration.get_password_hexdigest(inserts['password'])
        try:
            inserts['teams'] = ' '.join(inserts['teams'])
        except KeyError:
            pass
        inserts['description'] = inserts.pop('descr', None)
        keys = inserts.keys()
        sql = "INSERT INTO account(%s) VALUES(%s)" % (','.join(keys),
                                                      ','.join(['?']*len(keys)))
        self.execute(sql, *inserts.values())
        self.commit()
        raise HTTP_SEE_OTHER(Location=application.get_url('account',
                                                          inserts['name']))
        


class AccountCreateHtmlRepresentation(HtmlRepresentation):
    "HTML representation of the account create form page."

    def get_content(self):
        return self.get_form_panel()


EDIT_FIELDS = Fields(PasswordField('new_password', title='New password',
                                   descr='If blank, then password will'
                                         ' not be changed. If given, must be'
                                         ' at least 6 characters.'),
                     PasswordField('confirm_new_password',
                                   title='Confirm new password',
                                   descr='Must be given if a new password'
                                         ' is specified above.'),
                     MultiSelectField('teams', title='Teams',
                                      options=configuration.get_teams()),
                     IntegerField('max_tasks', title='Max number of tasks',
                                  required=True, default=100,
                                  descr='Maximum number of stored tasks.'
                                  ' Use -1 to denote no limit.'),
                     StringField('email', title='Email', length=30),
                     TextField('descr', title='Description'))


class GET_AccountEdit(GET_Mixin, GET):
    "Produce the edit form for an account."

    def __init__(self):
        super(GET_AccountEdit, self).__init__(
            outreprs=[JsonRepresentation(),
                      TextRepresentation(),
                      AccountEditHtmlRepresentation()],
            descr=self.__doc__)

    def is_access(self):
        return self.is_admin() or (self.login.name != 'anonymous' and
                                   self.login.name == self.account.name)

    def add_data(self, data, resource, request, application):
        self.account = self.get_account(resource.variables)
        if not self.account:
            raise HTTP_NOT_FOUND
        self.allow_access()
        data['title'] = "Edit account %s" % self.account.name
        values = dict(name=self.account.name,
                      email=self.account.email,
                      descr=self.account.description)
        # Only admin users are not allowed to edit teams and max_tasks
        fill = dict(teams=dict(options=configuration.get_teams()))
        fields_data = EDIT_FIELDS.get_data(fill=fill)
        if self.is_admin():
            values['teams'] = self.account.teams
            values['max_tasks'] = self.account.max_tasks
        else:
            for pos, field in enumerate(fields_data):
                if field['name'] == 'teams':
                    fields_data.pop(pos)
                    break
            for pos, field in enumerate(fields_data): # Must be a new loop!
                if field['name'] == 'max_tasks':
                    fields_data.pop(pos)
                    break
        data['form'] = dict(fields=fields_data,
                            values=values,
                            title='Modify account data',
                            href=resource.get_url(),
                            cancel=application.get_url('account',
                                                       self.account.name))


class AccountEditHtmlRepresentation(HtmlRepresentation):
    "HTML representation of the account edit form page."

    def get_content(self):
        return self.get_form_panel()


class POST_AccountEdit(POST_Mixin, POST):
    """Perform the edit on an account. The response consists of a
    HTTP 303 'See Other' redirection to the URL /account{account}.
    There is no output representation for this resource and method.
    """

    def __init__(self):
        super(POST_AccountEdit, self).__init__(infields=EDIT_FIELDS,
                                               descr=self.__doc__)

    def is_access(self):
        return self.is_admin() or (self.login.name != 'anonymous' and
                                   self.login.name == self.account.name)

    def action(self, resource, request, application):
        "Handle the request and return a response instance."
        self.account = self.get_account(resource.variables)
        if not self.account:
            raise HTTP_NOT_FOUND
        self.allow_access()
        updates = self.infields.parse(request)
        new_password = updates.pop('new_password')
        confirm_new_password = updates.pop('confirm_new_password')
        if new_password:
            if len(new_password) < 6:
                raise HTTP_BAD_REQUEST('password must contain at least 6 characters')
            if new_password != confirm_new_password:
                raise HTTP_BAD_REQUEST('new passwords not equal')
            updates['password'] = configuration.get_password_hexdigest(new_password)
        if self.is_admin():
            try:
                updates['teams'] = ' '.join(updates['teams'])
            except KeyError:
                pass
        else:
            updates.pop('teams', None)
            updates.pop('max_tasks', None)
        updates['description'] = updates.pop('descr', None)
        terms = ["%s=?" % key for key in updates.keys()]
        sql = "UPDATE account SET %s WHERE name=?" % ','.join(terms)
        values = updates.values()
        values.append(self.account.name)
        self.execute(sql, *values)
        self.commit()
        raise HTTP_SEE_OTHER(Location=application.get_url('account',
                                                          self.account.name))
