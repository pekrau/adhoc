""" Adhoc: Simple web application for task execution.

Site setup for the 'avatar2' machine; development.
"""

DEBUG = True

import whoyou
assert whoyou.__version__ == '12.2'     # Check package dependency
from whoyou import interface as users

ACCOUNT_BASE_URL_TEMPLATE = 'http://localhost/whoyou/account/%s/edit'

BLAST_PATH = '/home/pjk/ncbi-blast-2.2.25+/bin'
BLAST_VERSION = 'NCBI 2.2.25+ 32bit'
