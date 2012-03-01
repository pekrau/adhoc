""" Adhoc: Simple web application for task execution.

Return information for processes on the machine. Works for Linux and Unix.
"""

import os
import subprocess


class Usage(object):
    """Get command, CPU time and memory usage for a specified process.
    Method:
     update     obtain the current values from the system
    Attributes:
     cpu_time   cumulative CPU time, in seconds
     cpu_usage  instantaneous usage of CPU, in percent
     size       core image size, in physical pages
     rssize     resident set size; physical memory in kB
     vsize      virtual memory size, in kB
     command    executing command"""

    def __init__(self, pid=None, include_children=False):
        "PID may be integer or string."
        self.pid = pid or os.getpid()
        self.update(include_children=include_children)

    def __str__(self):
        return "%s: %s sec, %s%%, %s kB" % \
            (self.command, self.cpu_time, self.cpu_usage, self.vsize)

    def update(self, include_children=False):
        self.cpu_time = 0
        self.cpu_usage = 0.0
        self.size = 0
        self.rssize = 0
        self.vsize = 0
        args = ['/bin/ps',
                '-o', 'pid,cputime,pcpu,sz,rsz,vsz,args',
                '--no-heading',
                '--cumulative',
                '--pid', str(self.pid)]
        if include_children:
            args.append('--ppid')
            args.append(str(self.pid))
        process = subprocess.Popen(args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        data, error = process.communicate()
        if error or not data:
            raise ValueError("no such process %s" % self.pid)
        for line in data.split('\n'):
            parts = line.strip().split()
            if not parts: continue
            if parts[0] == str(self.pid):
                self.command = ' '.join(parts[6:])
            hours, minutes, seconds = parts[1].split(':')
            try:
                days, hours = hours.split('-')
                self.cpu_time = 86400 * int(days)
            except ValueError:
                self.cpu_time = 0.0
            self.cpu_time += 3600*int(hours) + 60*int(minutes) + int(seconds)
            self.cpu_usage += float(parts[2])
            self.size += int(parts[3])
            self.rssize += int(parts[4])
            self.vsize += int(parts[5])


if __name__ == '__main__':
    import sys
    for pid in sys.argv[1:]:
        print Usage(pid, include_children=False)
    print Usage(include_children=False)
