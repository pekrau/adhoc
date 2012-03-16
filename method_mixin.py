""" Adhoc: Simple web application for task execution.

Mixin class for methods: database connection and authentication.
"""

import sqlite3
import json

from wrapid.fields import *
from wrapid.response import *
from wrapid.resource import Resource, GET, POST, DELETE, RedirectMixin
from wrapid.login import LoginMixin

from . import configuration
from .database import Database, Task


class MethodMixin(LoginMixin):
    "Mixin class for Method subclasses: database connection and authentication."

    def prepare(self, resource, request, application):
        "Connect to the database, and set the data for the authenticated user."
        self.set_login(resource, request, application)
        self.db = Database()
        self.db.open()
        self.set_current(resource, request, application)
        self.check_access(application.name)

    def get_account(self, name, password=None):
        """Return a dictionary describing the account:
        name, description, email, teams and properties.
        If password is provided, authenticate the account.
        Raise KeyError if there is no such account.
        Raise ValueError if the password does not match.
        """
        return configuration.users.get_account(name, password)

    def get_account_anonymous(self):
        "Return the dictionary describing the anonymous account."
        return configuration.users.get_account('anonymous')

    def finalize(self):
        self.db.close()

    def set_current(self, resource, request, application):
        "Set the current entities to operate on."
        pass

    def set_current_account(self, resource, request, application):
        """Set the account to operate on; special case.
        This handles the case where an account name contains a dot
        and a short (<=4 chars) last name, which will otherwise
        be confused for a FORMAT specification.
        """
        variables = resource.variables
        try:
            self.account = self.get_account(variables['account'])
        except KeyError:
            if not variables.get('FORMAT'):
                raise HTTP_NOT_FOUND
            name = variables['account'] + variables['FORMAT']
            try:
                self.account = self.get_account(name)
            except KeyError:
                raise HTTP_NOT_FOUND
            else:
                resource.undo_format_specifier('account')

    def check_access(self, realm):
        """Check that login account may access this resource.
        Raise HTTP FORBIDDEN if login user is not allowed to read this.
        Raise HTTP_UNAUTHORIZED if anonymous user.
        """
        if not self.is_accessible():
            if self.login['name'] == 'anonymous':
                raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=realm)
            else:
                raise HTTP_FORBIDDEN("disallowed for '%(name)s'" % self.login)

    def is_accessible(self):
        "Is the login user allowed to access this method of the resource?"
        return True

    def is_login_admin(self):
        "Is the login user admin, or is member of admin team?"
        if self.login['name'] == 'admin': return True
        if 'admin' in self.login['teams']: return True
        return False

    def get_data_links(self, resource, request, application):
        "Return the links response data."
        links = []
        if self.is_login_admin():
            links.append(dict(title='All tasks',
                              href=application.get_url('tasks')))
        links.append(dict(title='My tasks',
                          href=application.get_url('tasks',
                                                   self.login['name'])))
        if self.is_login_admin():
            links.append(dict(title='All accounts',
                              href=application.get_url('accounts')))
        links.append(dict(title='My account',
                          href=application.get_url('account',
                                                   self.login['name'])))
        for tools in configuration.TOOLS:
            for tool in tools[1:]:
                links.append(dict(title="%(family)s: %(name)s" % tool,
                                  href=application.get_url(tool['name'])))
        links.append(dict(title='Documentation: API',
                          href=application.get_url('doc', 'API')))
        links.append(dict(title='Documentation: API tutorial',
                          href=application.get_url('doc', 'API_tutorial')))
        return links


class ToolMixin(object):
    "Mixin class for tool HTTP methods."

    tool = None

    def create_task(self):
        assert self.tool
        self.task = Task(self.db)
        self.task.tool = self.tool

    def check_quota(self, resource, request, application):
        "Check that account has not reached its usage quota."
        quotas = configuration.get_account_quotas(self.login)
        if quotas['ntasks'] < 0: return            # Negative quota = no limit.
        statistics = self.db.get_statistics(self.login['name'])
        if statistics['count'] >= quotas['ntasks']:
            raise HTTP_CONFLICT('account quota for number of tasks reached')

    def get_preferences(self):
        try:
            return self.login['properties']['Adhoc']['preferences'][self.tool]
        except KeyError:
            return dict()

    def set_preferences(self):
        "Update the login account preferences for the current Adhoc tool."
        assert self.tool
        if not self.inputs.get('set_preferences'): return
        try:
            properties = self.login['properties']['Adhoc']
        except KeyError:
            properties = dict()
        properties.setdefault('preferences', dict())[self.tool] = self.preferences
        configuration.users.update_account_properties(self.login['name'],
                                                      'Adhoc',
                                                      properties)
