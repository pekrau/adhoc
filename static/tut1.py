# tut1: Get the Adhoc top page.

import httplib

connection = httplib.HTTPConnection('tools.scilifelab.se')
connection.request('GET', '/adhoc')

response = connection.getresponse()
print 'HTTP status:', response.status, response.reason

representation = response.read()
print len(representation), 'bytes in representation from response'
