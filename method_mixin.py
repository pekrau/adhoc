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
        self.cnx = sqlite3.connect(configuration.ADHOC_DBFILE)
        loginname, password = basic_authentication(request, configuration.REALM)
        try:
            self.login = Account(self.cnx, loginname)
            self.login.check_password(password)
        except ValueError:
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=configuration.REALM)

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
        "Raise HTTP FORBIDDEN if login user is not allowed to read this."
        if not self.is_access():
            raise HTTP_FORBIDDEN('access disallowed for login account')

    def get_tasks_stats(self, account):
        "Return count of tasks and total tasks size for the account name."
        cursor = self.execute('SELECT COUNT(t.iui) FROM task AS t, account AS a'
                              ' WHERE t.account=a.id AND a.name=?', account)
        count = cursor.fetchone()[0]
        cursor = self.execute('SELECT SUM(t.size) FROM task AS t, account AS a'
                              ' WHERE t.account=a.id AND a.name=?', account)
        size = cursor.fetchone()[0] or 0
        return count, size


class Account(object):
    "Container for account data."

    def __init__(self, cnx, name):
        self.name = configuration.nstr(name)
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
        self.email = configuration.nstr(record[4])
        self.description = configuration.nstr(record[5])
        preferences = record[6]
        if preferences:
            self.preferences = configuration.nstr(json.loads(preferences))
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
                links.append(dict(title='Tasks',
                                  href=application.get_url('tasks')))
            links.append(dict(title='My tasks',
                              href=application.get_url('tasks',
                                                       self.login.name)))
            if self.is_admin():
                links.append(dict(title='Accounts',
                                  href=application.get_url('accounts')))
            links.append(dict(title='My account',
                              href=application.get_url('account',
                                                       self.login.name)))
            for tools in configuration.TOOLS:
                for tool in tools[1:]:
                    links.append(dict(title="%(family)s: %(name)s" % tool,
                                      href=application.get_url(tool['name'])))
            links.append(dict(title='API doc', href=application.get_url('doc')))

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
