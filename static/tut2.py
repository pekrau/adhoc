# tut2: Get the Adhoc top page in JSON format.

import httplib
import json

connection = httplib.HTTPConnection('tools.scilifelab.se')
connection.request('GET',
                   '/adhoc',
                   headers=dict(Accept='application/json'))

response = connection.getresponse()
print 'HTTP status:', response.status, response.reason
print 'Representation mimetype:', response.getheader('content-type')

representation = response.read()
data = json.loads(representation)
print 'Keys in data:', data.keys()
