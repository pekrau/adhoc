""" Adhoc web resource: simple bioinformatics tasks.

To do
=====

- add HMMER3 ?
- XXX not allowed Accounts page when admin login? tools site
- markdown in GET_Documentation
- __version__ in package __init__.py ? How access?
- version indicator in URL?
- when using WhoYou: preferences must be transferred one level down,
  under key 'Adhoc' (configuration.name)

- expand test suite

- script or web tool to add database
- allow redo of task?
  - edit and re-execute
  - or: copy task? including query
- investigate that BLAST bug using two NT databases; depends on specific db's?
"""

from configuration import VERSION as __version__
