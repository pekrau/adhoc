""" Adhoc: Simple web application for task execution.

Task execution.
"""

import os
import sys
import resource

from adhoc import configuration
from adhoc.database import Database, Task
from adhoc.daemonize import daemonize

# Set up tools lookup
import adhoc.blast


def execute():
    if len(sys.argv) != 2:
        sys.exit('no task IUI given')
    iui = sys.argv[1]
    try:
        db = Database()
        db.open()
        task = Task(db, iui=iui)
        if task.status != configuration.CREATED:
            raise ValueError("task status is not '%s'" % configuration.CREATED)
        task.status = configuration.EXECUTING
    except ValueError, msg:
        sys.exit(str(msg))
    finally:
        db.close()                      # Close before daemonizing

    daemonize(stdout=os.path.join(configuration.TASK_DIR, "%s.out" % iui),
              stderr=os.path.join(configuration.TASK_DIR, "%s.err" % iui))
    
    db.open()                           # Open again after daemonizing
    try:
        task = Task(db, iui=iui)
        try:
            tool = configuration.TOOLS_LOOKUP[task.tool]
        except KeyError:
            raise ValueError("no such tool '%s'" % task.tool)

        # The tool must save the pid of the process doing the heavy work.
        tool(task)

        task.cpu_time = 0.0
        for who in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN):
            usage = resource.getrusage(who)
            task.cpu_time += usage.ru_utime + usage.ru_stime
    except Exception, msg:
        task.data['error'] = "%s\n%s" % (task.data.get('error', ''), msg)
        task._status = configuration.FAILED
    finally:
        task.save()
        db.close()


if __name__ == '__main__':
    execute()
