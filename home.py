""" Adhoc web resource: simple bioinformatics tasks.

Home page.
"""

from wrapid.resource import *
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration
from .method_mixin import *
from .html_representation import HtmlRepresentation


class GET_Home(GET_Mixin, GET):
    "Produce the Adhoc home page."

    def __init__(self):
        super(GET_Home, self).__init__(
            outreprs=[JsonRepresentation(),
                      TextRepresentation(),
                      HtmlRepresentation()],
            descr=self.__doc__)

    def add_data(self, data, resource, request, application):
        data['title'] = "%s %s" % (application.name, application.version)
        loginname = data.get('loginname')
        if loginname and loginname != 'anonymous':
            login_descr = ''
        else:
            login_descr = '''- To login to your own account, use the button **Login** to the right. You can try things out without being logged in.'''
        data['descr'] = """
Various bioinformatics tools exposed as a task-oriented web resource
with a RESTful interface.

%s

- To view your current list of tasks, use the link **My tasks**
  in the left-hand side menu.

- To create a new task, use one of the tool links in the left-hand side menu.
  Enter the required data into the tool form and submit to create and execute
  the task.

Currently, the suite of BLAST programs are available. The list of BLAST
databases include some public standard data sets. Depending on the teams
that your account is a member of, some private databases may also be available.

**Important:** If you experience any problems with this site,
contact Per Kraulis with the relevant details, such as the exact
error message, the operation you attempted to perform, etc.

""" % login_descr
