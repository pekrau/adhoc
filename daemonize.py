""" Adhoc: Simple web application for task execution.

Module to fork the current process as a daemon.

NOTE: don't do any of this if your daemon gets started by inetd!
inetd does all you need, including redirecting standard file descriptors;
the chdir() and umask() steps are the only ones you may still want.

From: Python Cookbook, 2nd Edition. 
Credit: Juergen Hermann, Andy Gimblett, Josh Hoyt, Noah Spurrier,
Jonathan Bartlett, Greg Stein.
"""

import sys
import os


def daemonize(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    """Fork the current process as a daemon, redirecting standard file
    descriptors (by default, redirects them to /dev/null)."""
    # Perform first fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0) # Exit first parent.
    except OSError, e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)
    # Decouple from parent environment.
    os.chdir("/")
    os.umask(0)
    os.setsid()
    # Perform second fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0) # Exit second parent.
    except OSError, e:
        sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)
    # The process is now daemonized; redirect standard file descriptors.
    sys.stdout.flush()
    sys.stderr.flush()
    pid = os.getpid()
    if '%' in stdin:
        stdin = stdin % pid
    if '%' in stdout:
        stdout = stdout % pid
    if '%' in stderr:
        stderr = stderr % pid
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


def test_main(max_time=30):
    ''' Example main function: print a count & timestamp each second '''
    import time
    sys.stdout.write("Daemon started with pid %d\n" % os.getpid() )
    sys.stdout.write('Daemon stdout output\n')
    sys.stderr.write('Daemon stderr output\n')
    c = 0
    while True:
        sys.stdout.write("%d: %s\n" % (c, time.ctime()))
        sys.stdout.flush()
        c = c + 1
        if c >= max_time: break
        time.sleep(1)
    sys.stdout.write('done\n')
    sys.stdout.flush()


if __name__ == "__main__":
    daemonize(stdout='/tmp/daemon.log', stderr='/tmp/daemon.log')
    test_main()
