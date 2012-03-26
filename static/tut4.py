# tut4.py: Create a task using blastp, and wait until finished.

import httplib
import base64
import json
import urlparse
import time

ACCOUNT = 'test'
PASSWORD = 'abc123'
auth = "Basic %s" % base64.b64encode("%s:%s" % (ACCOUNT, PASSWORD))

data = dict(title='tut4 search',     # Optional title for task
            db='HUMAN.fasta',        # Name of Swiss-Prot human database
            query_content='MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTI',
            task_type='blastp-short',# Since above is a short peptide seq
            evalue=1.0 ,             # E-value cutoff
            outfmt=0)                # Output format: default listing

connection = httplib.HTTPConnection('tools.scilifelab.se')
connection.request('POST',
                   '/adhoc/blastp',
                   body=json.dumps(data),
                   headers={'Authorization': auth,
                            'Content-Type': 'application/json'}) # Body format

response = connection.getresponse()
print 'HTTP status:', response.status, response.reason
url = response.getheader('Location')
print 'Task URL:', url

url_parts = urlparse.urlsplit(url)

status_path = url_parts.path + '/status' # Path to status indicator resource
output_path = url_parts.path + '/output' # Path to output data

while True:                                          # Loop until finished
    connection = httplib.HTTPConnection('tools.scilifelab.se')
    connection.request('GET',
                       status_path,
                       headers={'Authorization': auth})
    response = connection.getresponse()
    status = response.read()
    if status not in ['waiting', 'executing']: break # Break when finished
    time.sleep(1)                                    # Poll once every second
print 'Final status:', status

connection = httplib.HTTPConnection('tools.scilifelab.se')
connection.request('GET',
                   output_path,
                   headers={'Authorization': auth})

response = connection.getresponse()
open('tut4_output.txt', 'w').write(response.read())
