""" Adhoc: Simple web application for task execution.

Mixin class for methods: database connection and authentication.
"""

import logging
import sqlite3
import json

from wrapid.fields import *
from wrapid.response import *
from wrapid.resource import Resource, GET, POST, DELETE
from wrapid.utils import basic_authentication, now, rstr, to_bool

from . import configuration


class MethodMixin(object):
    "Mixin class for Method subclasses: database connection and authentication."

    def prepare(self, resource, request, application):
        "Connect to the database, and set the data for the authenticated user."
        from .account import Account
        self.cnx = sqlite3.connect(configuration.MASTER_DB_FILE)
        try:
            name, password = basic_authentication(request,
                                                  application.name,
                                                  require=False)
            self.login = Account(self.cnx, name)
            self.login.check_password(password)
        except (KeyError, ValueError):
            # The following remedies an apparent deficiency of several
            # human browsers: For some pages in the site (notably
            # the root '/'), the authentication data does not seem to be
            # sent voluntarily by the browser.
            if request.cookie.has_key("%s-login" % application.name):
                raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=application.name)
            self.login = Account(self.cnx, 'anonymous')
        self.set_current(resource, request, application)
        self.check_access(application.name)

    def finalize(self):
        self.cnx.close()

    def set_current(self, resource, request, application):
        "Set the current entities to operate on."
        pass

    def check_access(self, realm):
        """Raise HTTP FORBIDDEN if login user is not allowed to read this.
        Raise HTTP_UNAUTHORIZED if anonymous user.
        """
        if not self.is_access():
            if self.login.name == 'anonymous':
                raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=realm)
            else:
                raise HTTP_FORBIDDEN("disallowed for login '%s'" %
                                     self.login.name)

    def is_access(self):
        "Is the login user allowed to access this method of the resource?"
        return True

    def is_login_admin(self):
        "Is the login user admin, or is member of admin team?"
        return self.login.name == 'admin' or 'admin' in self.login.teams

    def execute(self, sql, *values):
        cursor = self.cnx.cursor()
        logging.debug("adhoc: SQL '%s', values %s", sql, values)
        cursor.execute(sql, values)
        return cursor

    def commit(self):
        self.cnx.commit()

    def close(self):
        self.cnx.close()

    def get_data_basic(self, resource, request, application):
        "Return a dictionary with the basic data for the resource."
        links = []
        if self.is_login_admin():
            links.append(dict(title='All tasks',
                              href=application.get_url('tasks')))
        links.append(dict(title='My tasks',
                          href=application.get_url('tasks',
                                                   self.login.name)))
        if self.is_login_admin():
            links.append(dict(title='All accounts',
                              href=application.get_url('accounts')))
        links.append(dict(title='My account',
                          href=application.get_url('account',
                                                   self.login.name)))
        for tools in configuration.TOOLS:
            for tool in tools[1:]:
                links.append(dict(title="%(family)s: %(name)s" % tool,
                                  href=application.get_url(tool['name'])))
        links.append(dict(title='Documentation: API',
                          href=application.get_url('doc', 'API')))
        links.append(dict(title='Documentation: API tutorial',
                          href=application.get_url('doc', 'API_tutorial')))

        return dict(application=dict(name=application.name,
                                     version=application.version,
                                     href=application.url,
                                     host=configuration.HOST),
                    resource=resource.type,
                    href=resource.url,
                    links=links,
                    outreprs=self.get_outrepr_links(resource, application),
                    loginname=self.login.name)

    def get_account(self, variables):
        """Get the account instance according to the variables data.
        Handle the case where an account name containing a dot and
        a short (<=4 chars) last name, which will be confused for
        a format specification.
        Returns None if no account could be identified.
        """
        from .account import Account
        try:
            return Account(self.cnx, variables['account'])
        except KeyError:
            return None
        except ValueError:
            if variables.get('FORMAT'):
                name = variables['account'] + variables['FORMAT']
                try:
                    result = Account(self.cnx, name)
                except ValueError:
                    return None
                else:
                    variables['account'] += variables['FORMAT']
                    variables['FORMAT'] = None
                    return result
        return None

    def get_tasks_stats(self, account):
        "Return count of tasks and total tasks size for the account name."
        cursor = self.execute('SELECT COUNT(t.iui) FROM task AS t, account AS a'
                              ' WHERE t.account=a.id AND a.name=?', account)
        count = cursor.fetchone()[0]
        cursor = self.execute('SELECT SUM(t.size) FROM task AS t, account AS a'
                              ' WHERE t.account=a.id AND a.name=?', account)
        size = cursor.fetchone()[0] or 0
        return count, size

    def update_account_preferences(self):
        if not self.inputs.get('set_preferences'): return
        self.login.preferences[self.tool] = self.new_preferences
        self.execute('UPDATE account SET preferences=? WHERE name=?',
                     json.dumps(self.login.preferences),
                     self.login.name)
        self.commit()


class RedirectMixin(object):
    "Mixin providing a redirect response."

    def get_response(self, resource, request, application):
        "Redirect to a previously specified URL."
        return HTTP_SEE_OTHER(Location=self.redirect)
