## Adhoc: A simple web application for task execution

This web application is an interface to various third-party software,
which are made available as a set of tools for executing specific tasks.

### Available tools

The set of **BLAST** programs for searching biomolecule
sequence databases is available. The list of BLAST databases
includes some public standard data sets. Depending on the teams
that your account is a member of, some private databases may
also be available.

Other tools can be implemented as the need arises. Contact the administrator.

### Databases

The databases for the tools are managed by the administrator.
It is currently not possible for a user to upload a database
through the web interface. The access to the databases is
controlled by the team memberships of a user account.

Contact the administrator if you wish to make additional databases
available, or if your memberships should be changed.

### Usage

Each software executable is represented as a **tool**. The tool page
contains input fields to define a **task** to be executed by the tool.
The user provides the input and submits the task, which is then
executed by the server in the background.

Each task is identified by a IUI (Instance Unique Identifier),
which is a string of 32 characters, visible in the URL of the task.
The user can bookmark this URL to view the task and check its current
status at any time. When the task has finished, the output can be
viewed or downloaded. A task is persistent; it is stored on the server
until explicitly deleted by the user.

In the current implementation, the execution is simply done in
the background on the server. Other implementations may use a
queueing system and/or execute the tasks on other back-end machines.

### Login

Usually, a user logs in to an account before using the system.
Any tasks created will then be private, and some private databases
may become available, depending on the team memberships of
the user's account.

It is possible to use the Adhoc system without logging in, in which case
the built-in account 'anonymous' is used. All its tasks are publicly
available, and only public databases are available to it.

Contact the administrator of the server to obtain your own account.

### RESTful interface

The Adhoc web interface is RESTful, meaning that scripts can easily
be written to access the system from other machines.

### Implementation

The system is written in Python 2.6. The following source code
packages are needed:.

- [https://github.com/pekrau/adhoc](https://github.com/pekrau/adhoc):
  Source code for the **Adhoc** system.
- [https://github.com/pekrau/wrapid](https://github.com/pekrau/wrapid):
  Package **wrapid** providing the web service framework.
- [http://pypi.python.org/pypi/Markdown](http://pypi.python.org/pypi/Markdown):
  Package for producing HTML from text using the simple markup
  language [Markdown](http://daringfireball.net/projects/markdown/).
- [https://github.com/pekrau/whoyou](https://github.com/pekrau/whoyou):
  Package **WhoYou** providing basic authentication services.
  This can in principle be exchanged for another system.

The **Sqlite3** database system is used as storage back-end in the current
implementation. It is included in the standard Python distribution.

An example installation can be viewed at
[http://tools.scilifelab.se/adhoc](http://tools.scilifelab.se/adhoc).
