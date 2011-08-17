""" Adhoc web resource.

Home page: listing of current tasks for logged-in user.
"""

from .webresource import *


class Home(WebResource):
    "Home page."

    def GET(self, request, response):
        from .task import get_tasks
        html = HtmlRepresentation(self, 'Adhoc')
        html.abstract = P('Task-oriented web interface to various bioinformatics tools.')
        url = configuration.get_url('tasks', self.user['name'])
        html.append_markdown('''Currently, the suite of BLAST programs are
available.

The available databases include some public standard data sets,
and possibly some private data sets depending on the teams that
your account is a member of.

To view your current list of tasks, click [here](%s),
or on the item **My tasks** in the menu at the left.''' % url)
        html.write(response)
