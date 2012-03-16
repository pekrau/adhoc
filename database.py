""" Adhoc: Simple web application for task execution.

Database interface classes.
"""

import logging
import sqlite3
import json
import os
import uuid
import signal

from wrapid.utils import now, rstr

from adhoc import configuration
from adhoc.usage import Usage


class Database(object):
    "Interface to the database."

    def __init__(self):
        self.path = configuration.MASTER_DB_FILE

    def open(self):
        assert not self.opened
        self.cnx = sqlite3.connect(self.path)
        self.cnx.text_factory = str

    def close(self):
        try:
            self.cnx.close()
        except AttributeError:
            pass
        else:
            del self.cnx

    @property
    def opened(self):
        return hasattr(self, 'cnx')

    def execute(self, sql, *values):
        assert self.opened
        logging.debug("SQL> %s %s", sql, values)
        cursor = self.cnx.cursor()
        cursor.execute(sql, values)
        return cursor

    def commit(self):
        assert self.opened
        self.cnx.commit()

    def rollback(self):
        assert self.opened
        self.cnx.rollback()

    def create(self):
        assert not self.opened
        if os.path.exists(self.path):
            raise IOError('cannot overwrite existing database file')
        if os.path.exists(configuration.TASK_DIR):
            if not os.path.isdir(configuration.TASK_DIR):
                raise IOError('cannot create task directory')
        else:
            os.mkdir(configuration.TASK_DIR)
        self.open()
        self.execute('CREATE TABLE task'
                     '(id INTEGER PRIMARY KEY,'
                     ' iui TEXT UNIQUE NOT NULL,'
                     ' tool TEXT NOT NULL,'
                     ' title TEXT,'
                     ' status TEXT NOT NULL,'
                     ' pid INTEGER,'
                     ' size INTEGER,'
                     ' cpu_time REAL,'
                     ' account TEXT NOT NULL,'
                     ' modified TEXT NOT NULL)')
        self.execute('CREATE INDEX task_account_index ON task(account)')
        self.commit()

    def get_tasks(self, owner=None):
        """Return a generator to iterate over all Task instances.
        Restrict to those owned by the named account, if given.
        """
        # XXX filter by access for an account?
        values = []
        sql = 'SELECT iui FROM task'
        if owner:
            sql += ' WHERE account=?'
            values.append(owner)
        sql += ' ORDER BY modified DESC'
        cursor = self.execute(sql, *values)
        for (iui,) in cursor:
            yield Task(self, iui=iui)

    def get_statistics(self, account):
        "Return the current statistics for the named account."
        sql = 'SELECT COUNT(*) FROM task WHERE account=?'
        cursor = self.execute(sql, account)
        result = dict(count=cursor.fetchone()[0])
        sql = 'SELECT SUM(size) FROM task WHERE account=?'
        cursor = self.execute(sql, account)
        result['size'] = cursor.fetchone()[0] or 0
        sql = 'SELECT SUM(cpu_time) FROM task WHERE account=?'
        cursor = self.execute(sql, account)
        result['cpu_time'] = cursor.fetchone()[0] or 0.0
        return result


class Task(object):
    "Task container and execution manager."

    def __init__(self, db, iui=None):
        assert db
        self.db = db
        if iui is None:
            self.id = None
            self.iui = None
            self.tool = None
            self.title = None
            self._status = None
            self._pid = None
            self.size = None
            self.cpu_time = None
            self.account = None
            self._data = None
            self.modified = None
        else:
            self.fetch(iui)

    def __str__(self):
        return "%s task: %s" % (self.tool, self.title or '[no title]')

    def fetch(self, iui):
        "Raise KeyError if no such task."
        cursor = self.db.execute('SELECT id,tool,title,status,pid,'
                                 ' size,cpu_time,account,modified'
                                 ' FROM task WHERE iui=?', iui)
        record = cursor.fetchone()
        if not record:
            raise KeyError("no such task %s" % iui)
        self.id = record[0]
        self.iui = iui
        self.tool = record[1]
        self.title = record[2]
        self._status = record[3]
        self._pid = record[4]
        self.size = record[5] or 0
        self.cpu_time = record[6] or 0.0
        self.account = record[7]
        self.modified = record[8]
        self._data = None

    def create(self, account):
        assert self.id is None
        assert account
        self.iui = uuid.uuid4().hex
        self._status = configuration.CREATED
        self.account = account
        self.write_data()
        self.modified = now()
        cursor = self.db.execute('INSERT INTO task(iui,tool,title,status,'
                                 ' pid,size,cpu_time,account,modified)'
                                 ' VALUES(?,?,?,?,?,?,?,?,?)',
                                 self.iui,
                                 self.tool,
                                 self.title,
                                 self.status,
                                 self.pid,
                                 self.size,
                                 self.cpu_time,
                                 self.account,
                                 self.modified)
        self.id = cursor.lastrowid
        self.db.commit()

    def save(self, data=True):
        assert self.id
        if data:
            self.write_data()
        self.modified = now()
        self.db.execute('UPDATE task SET title=?,status=?,pid=?,'
                        ' size=?,cpu_time=?,modified=? WHERE id=?',
                        self.title,
                        self.status,
                        self.pid,
                        self.size,
                        self.cpu_time,
                        self.modified,
                        self.id)
        self.db.commit()

    def write_data(self):
        assert self.iui
        filename = os.path.join(configuration.TASK_DIR, self.iui)
        outfile = open(filename, 'w')
        json.dump(self.data, outfile)
        outfile.close()
        self.size = os.path.getsize(filename)

    def get_pid(self):
        return self._pid

    def set_pid(self, new):
        self._pid = new
        self.save(data=False)

    pid = property(get_pid, set_pid)

    def get_status(self):
        return self._status

    def set_status(self, new):
        self._status = new
        self.save(data=False)

    status = property(get_status, set_status)

    @property
    def data(self):
        if self._data is None:
            if self.iui:
                infile = open(os.path.join(configuration.TASK_DIR, self.iui))
                self._data = rstr(json.load(infile))
                infile.close()
            else:
                self._data = dict()
        return self._data

    def delete(self):
        assert self.id
        if self.status == configuration.EXECUTING:
            try:
                os.kill(self.pid, signal.SIGKILL)
            except OSError:
                pass
        self.db.execute('DELETE FROM task WHERE id=?', self.id)
        self.db.commit()
        os.remove(os.path.join(configuration.TASK_DIR, self.iui))
        try:
            os.remove(os.path.join(configuration.TASK_DIR, "%s.out"% self.iui))
        except OSError:
            pass
        try:
            os.remove(os.path.join(configuration.TASK_DIR, "%s.err"% self.iui))
        except OSError:
            pass

    def get_data(self, application=None, full=True):
        result = dict(iui=self.iui,
                      tool=self.tool,
                      title=self.title,
                      status=dict(value=self.status),
                      size=self.size,
                      cpu_time=self.cpu_time,
                      account=self.account,
                      modified=self.modified)
        if self.status == configuration.EXECUTING and self.pid:
            usage = Usage(pid=self.pid, include_children=True)
            result['cpu_time'] = usage.cpu_time
        if application:
            result['href'] = href = application.get_url('task', self.iui)
            result['status']['href'] = href + '/status'
        else:
            href = None
        if full:
            result.update(self.data)
            content = result.pop('query')
            query = dict(content=content,
                         size=len(content or ''),
                         # XXX fix this for the general case
                         ## mimetype=data['task'].pop('query_content_type'),
                         mimetype='text/plain')
            if href:
                query['href'] = href + '/query'
            result['query'] = query
            content = result.pop('output', None)
            if content is not None:
                output = dict(content=content,
                              size=len(content),
                              mimetype=result.pop('output_content_type'))
                if href:
                    output['href'] = href + '/output'
                result['output'] = output
        return result


if __name__ == '__main__':
    import sys
    db = Database()
    try:
        db.create()
    except IOError, msg:
        print msg
        sys.exit(1)
    print 'Adhoc database created.'
