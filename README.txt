adhoc is a web application for executing tasks.

As the name implies, it is used to interface to various software as
appropriate.

The use-case model is that the software is represented by a tool
which presents a page (or possibly multiple pages) for input.

When the requried input has been provided, the task is created and
given a UUID, and is then executed by the system.

The user can view the task and check its current status. When
finished, the output can be viewed or downloaded.

The adhoc web interface is RESTful, meaning that scripts can easily be
written to access the system.

The databases needed by the tools are defined by the administrator,
who can set up access control for the accounts to the databases by a
team membership mechanism.

Currently, the execution is simply done in the background. A queueing
system should be possible to slot into place when the need arises.

/Per Kraulis
