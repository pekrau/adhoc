# tut5: Delete a task, whose URL must be known.

import httplib
import base64

ACCOUNT = 'test'
PASSWORD = 'abc123'
auth = "Basic %s" % base64.b64encode("%s:%s" % (ACCOUNT, PASSWORD))

connection = httplib.HTTPConnection('tools.scilifelab.se')
connection.request('DELETE',
                   '/adhoc/task/17c44f332cbb45ae918188b98c28c000',
                   headers={'Authorization': auth})

response = connection.getresponse()
print 'HTTP status:', response.status, response.reason
