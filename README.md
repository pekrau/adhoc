## Adhoc: Simple web application for task execution

This web application is an interface to various third-party
software as appropriate.

### Usage

Each software executable is represented as a **tool**. The tool page
contains input fields to define a **task** to be executed by the tool.
The user provides the input and submits the task, which is then
executed by the server in the background.

Each task is identified by a IUI (Instance Unique Identifier),
which is a string of 32 characters, visible in the URL of the task.
The user can view the task and check its current status at any time.
When the task has finished, the output can be viewed or downloaded.
A task is persistent; it is stored on the server until explicitly
deleted by the user.

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

Contact the administrator of your site to obtain your own account.

### Current tools

The **BLAST** suite of programs for searching biomolecule
sequence databases is available. The list of BLAST databases
includes some public standard data sets. Depending on the teams
that your account is a member of, some private databases may
also be available.

Other tools can be implemented as the need arises. Contact the administrator.

### RESTful interface

The Adhoc web interface is RESTful, meaning that scripts can easily
be written to access the system.

### Databases

The databases for the tools are managed by the administrator.
It is currently not possible for a user to upload a database
through the web interface. The access to the databases is
controlled by the team memberships of a user account.

Contact the administrator if you wish to make additional databases
available, or if your memberships should be changed.

### Implementation

The Sqlite3 database system is used as storage back-end in the current
implementation.

The Adhoc source code lives at
[https://github.com/pekrau/adhoc](https://github.com/pekrau/adhoc).
It relies on the packages **wrapid** at
[https://github.com/pekrau/wrapid](https://github.com/pekrau/wrapid)
and **HyperText** at
[https://github.com/pekrau/HyperText](https://github.com/pekrau/HyperText).

An example installation can be viewed at
[http://tools.scilifelab.se/webtables](http://tools.scilifelab.se/adhoc).
