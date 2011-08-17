""" Adhoc web resource.

Home page: listing of current tasks for logged-in user.
"""

from .webresource import *


class Home(WebResource):
    "Home page."

    def GET(self, request, response):
        from .task import get_tasks
        html = HtmlRepresentation(self, 'Adhoc')
        html.abstract = P('Web interface to various tools for'
                          ' analysis of different data sets.')
        url = configuration.get_url('tasks')
        html.append_markdown('''Currently, the suite of BLAST programs are
available, with a few standard databases.

To view your current list of tasks, click [here](%s),
or on the item **My tasks** in the menu at the left.''' % url)
        html.write(response)
