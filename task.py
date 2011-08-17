""" Adhoc web resource.

Task container and execution manager.
"""

import os
import signal
import sys
import uuid
import json
import sqlite3
import resource

from adhoc import configuration
from adhoc.daemonize import daemonize

# Set up tools lookup
import adhoc.blast


def get_tasks(cnx, account=None):
    "Get all tasks; for the account (user id), if given."
    values = []
    sql = 'SELECT iui FROM task'
    if account:
        sql += ' WHERE account=?'
        values.append(account)
    sql += ' ORDER BY modified DESC'
    cursor = cnx.cursor()
    cursor.execute(sql, tuple(values))
    result = []
    for record in cursor:
        result.append(Task(cnx, record[0]))
    return result


class Task(object):
    "Task container and execution manager."

    def __init__(self, cnx, iui=None):
        self.cnx = cnx
        if iui is None:
            self.id = None
            self.iui = uuid.uuid4().hex
            self.tool = None
            self.title = None
            self.status = 'created'
            self.pid = None
            self.size = None
            self.account = None
            self.modified = None
            self.data = dict()
        else:
            self.load(iui)

    def __str__(self):
        if self.title:
            return "%s task: %s" % (self.tool, self.title)
        else:
            return "%s task" % self.tool

    def get_url(self, *parts, **params):
        parts = ['task', self.iui] + list(parts)
        return configuration.get_url(*parts, **params)

    def execute(self, sql, *values):
        cursor = self.cnx.cursor()
        cursor.execute(sql, values)
        return cursor

    def load(self, iui):
        self.iui = iui
        cursor = self.execute('SELECT id,tool,title,status,pid,size,account,'
                              ' modified FROM task WHERE iui=?', self.iui)
        record = cursor.fetchone()
        if not record:
            raise ValueError("no such task %s" % self.iui)
        self.id = record[0]
        self.tool = record[1]
        self.title = record[2]
        self.status = record[3]
        self.pid = record[4]
        self.size = record[5]
        self.account = record[6]
        self.modified = record[7]
        infile = open(os.path.join(configuration.TASK_DIR, self.iui))
        self.data = json.load(infile)
        infile.close()

    def create(self, account):
        assert self.iui
        assert self.id is None
        self.account = account
        self.modified = configuration.now()
        cursor = self.execute('INSERT INTO task(iui,tool,title,status,pid,'
                              'account,modified) VALUES(?,?,?,?,?,?,?)',
                              self.iui,
                              self.tool,
                              self.title,
                              self.status,
                              self.pid,
                              self.account,
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
        if self.status == 'executing':
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


def execute():
    if len(sys.argv) != 2:
        sys.exit('no task IUI given')
    iui = sys.argv[1]
    try:
        cnx = sqlite3.connect(configuration.ADHOC_FILE)
        task = Task(cnx, iui)
        if task.status != 'created':
            raise ValueError("task status is not 'created'")
        task.set_status('executing')
    except ValueError, msg:
        sys.exit(str(msg))
    finally:
        cnx.close()                     # Close before daemonizing

    daemonize(stdout=os.path.join(configuration.TASK_DIR, "%s.out" % iui),
              stderr=os.path.join(configuration.TASK_DIR, "%s.err" % iui))
    
    cnx = sqlite3.connect(configuration.ADHOC_FILE) # Open after daemonizing
    try:
        task = Task(cnx, iui)
        task.set_pid(os.getpid())
        try:
            tool = configuration.TOOLS_LOOKUP[task.tool]
        except KeyError:
            raise ValueError("no such tool '%s'" % task.tool)
        tool(task)
        result = 0.0
        for who in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN):
            usage = resource.getrusage(who)
            result += usage.ru_utime + usage.ru_stime
        task.data['cpu_time'] = result
        task.save()
    except Exception, msg:
        task.data['error'] = "%s\n%s" % (task.data.get('error', ''), msg)
        task.set_status('failed')
    finally:
        cnx.close()


if __name__ == '__main__':
    execute()
