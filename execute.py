""" Adhoc web resource: simple bioinformatics tasks.

Task execution.
"""

import os
import sys
import resource
import sqlite3

from adhoc import configuration
from adhoc.task import Task
from adhoc.daemonize import daemonize

# Set up tools lookup
import adhoc.blast


def execute():
    if len(sys.argv) != 2:
        sys.exit('no task IUI given')
    iui = sys.argv[1]
    try:
        cnx = sqlite3.connect(configuration.MASTER_DBFILE)
        task = Task(cnx, iui)
        if task.status != configuration.CREATED:
            raise ValueError("task status is not '%s'" % configuration.CREATED)
        task.set_status(configuration.EXECUTING)
    except ValueError, msg:
        sys.exit(str(msg))
    finally:
        cnx.close()                     # Close before daemonizing

    daemonize(stdout=os.path.join(configuration.TASK_DIR, "%s.out" % iui),
              stderr=os.path.join(configuration.TASK_DIR, "%s.err" % iui))
    
    cnx = sqlite3.connect(configuration.MASTER_DBFILE) # Open after daemonizing
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
        task.set_status(configuration.FAILED)
    finally:
        cnx.close()


if __name__ == '__main__':
    execute()
