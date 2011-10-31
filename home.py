""" Adhoc web resource: simple bioinformatics tasks.

Home page.
"""

from wrapid.resource import *

from . import configuration
from .method_mixin import *
from .json_representation import JsonRepresentation
from .text_representation import TextRepresentation
from .html_representation import HtmlRepresentation


class GET_Home(GET_Mixin, GET):
    "Return the Adhoc home page."

    def __init__(self):
        super(GET_Home, self).__init__(
            outreprs=[JsonRepresentation(),
                      TextRepresentation(),
                      HtmlRepresentation()],
            descr=self.__doc__)

    def add_data(self, data, resource, request, application):
        data['title'] = "%s %s" % (application.name, application.version)
        data['descr'] = '''
Updated 27 Oct 2011 !
---------------------

**If you experience any problems, contact Per Kraulis with the details,
such as exact error message, attempted operation, etc.**

Various bioinformatics tools exposed as a task-oriented web resource
with a RESTful interface.

To create a new task, use one of the tool links in the left-hand side menu.
Enter the required data into the tool form and submit to create and execute
the task.

To view your current list of tasks, use the link **My tasks**
in the left-hand side menu.

Currently, the suite of BLAST programs are available. The list of BLAST
databases include some public standard data sets. Depending on the teams
that your account is a member of, some private databases may also be available.
'''
