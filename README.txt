adhoc is a web system for executing tasks.

As the name implies, it is used to interface to various software as
appropriate. The model is that the software is represented by a tool
which presents a page (or possibly multiple pages) for input. When the
requried input has been provided, the task is created and given a
UUID, and is then executed by the system.

A user must log in to an account to use the system.

The adhoc web interface is RESTful, meaning that scripts can be used to
access the system.

Currently, the execution is simply done in the background. A queueing
system should be possible to slot into place when the need arises.

The user can view the task and check its current status. When
finished, the output can be viewed or downloaded.

The databases needed by the tools are defined by the administrator,
who can set up access control for the accounts to the databases by a
team membership mechanism.

/Per Kraulis
