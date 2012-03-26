# tut3.py: How to authenticate as a given account.

import httplib
import json
import base64

ACCOUNT = 'test'
PASSWORD = 'abc123'
auth = "Basic %s" % base64.b64encode("%s:%s" % (ACCOUNT, PASSWORD))

connection = httplib.HTTPConnection('tools.scilifelab.se')
connection.request('GET',
                   '/adhoc/tasks/test',
                   headers={'Accept': 'application/json',
                            'Authorization': auth})

response = connection.getresponse()
print 'HTTP status:', response.status, response.reason

if response.status == 200:
    representation = response.read()
    data = json.loads(representation)
    print 'Keys in data:', data.keys()
