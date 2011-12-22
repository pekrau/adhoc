""" Adhoc web resource: simple bioinformatics tasks.

Mixin classes for methods: database connection, authentication, etc.
"""

import logging
import sqlite3
import json

from wrapid.utils import basic_authentication
from wrapid.response import (HTTP_UNAUTHORIZED_BASIC_CHALLENGE,
                             HTTP_FORBIDDEN)

from . import configuration


class BaseMixin(object):
    "Base mixin class; database connection, authentication, etc."

    def connect(self, resource, request, application):
        "Connect to the database, and set the data for the authenticated user."
        from .account import Account
        self.cnx = sqlite3.connect(configuration.MASTER_DBFILE)
        try:
            name, password = basic_authentication(request,
                                                  configuration.REALM,
                                                  require=False)
            self.login = Account(self.cnx, name)
            self.login.check_password(password)
            logging.info("adhoc: direct login")
        except (KeyError, ValueError):
            # The following remedies an apparent deficiency of several
            # human browsers: For some pages in the site (notably
            # the root '/'), the authentication data does not seem to be
            # sent voluntarily by the browser.
            if request.cookie.has_key("%s-login" % configuration.NAME):
                logging.info("adhoc: not logged in, but cookie %s-login" % configuration.NAME)
                raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=configuration.REALM)
            self.login = Account(self.cnx, 'anonymous')
            logging.info("adhoc: anonymous login")

    def execute(self, sql, *values):
        cursor = self.cnx.cursor()
        logging.debug("adhoc: SQL '%s', values %s", sql, values)
        cursor.execute(sql, values)
        return cursor

    def commit(self):
        self.cnx.commit()

    def close(self):
        self.cnx.close()

    def is_admin(self):
        "Is the login user admin, or is member of admin team?"
        return self.login.name == 'admin' or 'admin' in self.login.teams

    def allow_admin(self):
        "Raise HTTP FORBIDDEN if login user is not admin."
        if not self.is_admin():
            raise HTTP_FORBIDDEN("'admin' login required")

    def is_access(self):
        "Is the login user allowed to access this method of the resource?"
        return True

    def allow_access(self):
        """Raise HTTP FORBIDDEN if login user is not allowed to read this.
        Raise HTTP_UNAUTHORIZED if anonymous user.
        """
        if not self.is_access():
            if self.is_anonymous():
                raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=configuration.REALM)
            else:
                raise HTTP_FORBIDDEN("disallowed for login '%s'" %
                                     self.login.name)

    def is_anonymous(self):
        "Is the login user 'anonymous'?"
        return self.login.name == 'anonymous'

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


class GET_Mixin(BaseMixin):

    def get_data(self, resource, request, application):
        self.connect(resource, request, application)
        try:
            # XXX the values should be taken from 'configuration'
            host = dict(title='SciLifeLab tools',
                        href='http://tools.scilifelab.se/',
                        contact='Per Kraulis',
                        email='per.kraulis@scilifelab.se')

            appl = dict(name=application.name,
                        version=application.version,
                        href=application.url,
                        host=host)

            links = []
            if self.is_admin():
                links.append(dict(title='All tasks',
                                  href=application.get_url('tasks')))
            links.append(dict(title='My tasks',
                              href=application.get_url('tasks',
                                                       self.login.name)))
            if self.is_admin():
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

            outreprs = self.get_outreprs_links(resource, request, application)

            data = dict(application=appl,
                        href=resource.url,
                        links=links,
                        outreprs=outreprs,
                        loginname=self.login.name)
            self.add_data(data, resource, request, application)
            return data
        finally:
            self.close()

    def add_data(self, data, resource, request, application):
        raise NotImplementedError


class POST_Mixin(BaseMixin):

    def __call__(self, resource, request, application):
        self.connect(resource, request, application)
        try:
            self.action(resource, request, application)
        finally:
            self.close()

    def action(self, resource, request, application):
        raise NotImplementedError

    def update_account_preferences(self):
        if not self.inputs.get('set_preferences'): return
        self.login.preferences[self.tool] = self.new_preferences
        self.execute('UPDATE account SET preferences=? WHERE name=?',
                     json.dumps(self.login.preferences),
                     self.login.name)
        self.commit()
