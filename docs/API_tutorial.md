The Application Programming Interface for this web application is designed
according to the RESTful architectural style. Any client program or software
that can speak HTTP can therefore be used to interact with the system.

In this tutorial we will use Python and its standard module
[httplib](http://docs.python.org/library/httplib.html).
This is a very basic HTTP interaction module. It has the advantage
of showing explicitly the mechanism of HTTP interactions.

There are more powerful Python modules for HTTP interactions,
such as [urllib](http://docs.python.org/library/urllib.html)
or [urllib2](http://docs.python.org/library/urllib2.html).
The information presented here is useful also in those cases.

Obtaining a document from the web service
-----------------------------------------

Let us obtain a document given a known URL.
In this [Python code](../static/tut1.py) example, we simply
get the top page for the Adhoc web site:

    # tut1: Get the Adhoc top page.

    import httplib

    connection = httplib.HTTPConnection('tools.scilifelab.se')
    connection.request('GET', '/adhoc')

    response = connection.getresponse()
    print 'HTTP status:', response.status, response.reason

    representation = response.read()
    print len(representation), 'bytes in representation from response'

This example illustrates several points:

1. The httplib module requires that we split up the URL
   into its components netloc ('tools.scilifelab.se') and path ('/adhoc').
   This would not be necessary when using urllib or urllib2.
   The scheme 'http' is implied.
2. The request must include the explicit HTTP method, in this case 'GET'.
3. The response has a status code. The possible status code values are
   defined by HTTP. In this case we get 200, which translates to 'OK'.
4. The representation is included in the response, and is obtained using
   the 'read' method of the response instance.

A peculiar quirk of the httplib package is that once a connection instance
has been used for a single request/response cycle, it becomes useless.
One must create a new connection instance to perform another request.

Requesting a particular representation format
---------------------------------------------

There are two ways of requesting a particular format of the representation:

1. Specify the acceptable mimetype in the request using a HTTP header.
2. Append the appropriate suffix (file type extension) to the URL.

The first method is more general and HTTP-ish. As in this
[Python code](../static/tut2.py):

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

We tell the server that we can accept only JSON format by specifying
the mimetype 'application/json' in the 'Accept' header of the request,
as defined by HTTP.

The representation is sent as a JSON data structure. We verify this by looking
at the 'Content-Type' header of the response.

We convert the JSON representation to a Python data structure using
the 'loads' function of the standard
[json](http://docs.python.org/library/json.html) module.
We happen to know that it is a dictionary, and we therefore print the keys
of that dictionary to have a look at what we got.

Adding login information to a request
-------------------------------------

The previous requests were done without login, so the Adhoc system viewed
these as done under the account 'anonymous'. For most activities in Adhoc,
you will want to login to your own account. Thus, authentication is needed
for login.

Due to the stateless nature of the HTTP protocol, the authentication
data (user account and password) has to be included in every request.

The Adhoc system currently uses only Basic Authentication. In cases where
security is an important issue, TLS should therefore be used (i.e. the https
scheme, using HTTP over an encrypted connection).

HTTP Basic Authentication works by packaging the user account name and
the password together into a base64 message, and adding this as a header
to the HTTP request, as in this [Python code](../static/tut3.py):

    # tut3: How to authenticate as a given account.

    import httplib
    import json
    import base64

    ACCOUNT = 'test'
    PASSWORD = 'abc123'
    auth = "Basic %s" % base64.b64encode("%s:%s" % (ACCOUNT, PASSWORD))

    connection = httplib.HTTPConnection('tools.scilifelab.se')
    connection.request('GET',
                       '/adhoc/tasks/test',
                       headers=dict(Accept='application/json',
                                    Authorization=auth))
    response = connection.getresponse()
    print 'HTTP status:', response.status, response.reason

    if response.status == 200:
        representation = response.read()
        data = json.loads(representation)
        print 'Keys in data:', data.keys()

Try this with the wrong password, and you will get the response status 401
'Unauthorized'.

Creating a task
---------------

Now for some real work. We want to use BLAST to search a nucleotide query
against a nucleotide database. The [blastp](../blastp) tool does that.

The basic idea with the Adhoc web service is that one does a HTTP POST to
the chosen tool with all required input data in an appropriate representation.
The Adhoc system creates a task and launches it, and responds by sending
a HTTP Redirect containing the URL of the newly created task.
The task is executed on the server asynchronously, and the client script
will have to poll the task now and then until it has finished.

In order to figure out what input is required for a tool, look at the page
for that tool using an ordinary browser. The input parameters for the tool
are described there.

For the exact names of the input parameters, one can look at the appropriate
section in the documentation page for [the API](API).

One should also look in the TXT representation of the tool page,
since the parameters and the allowed options are listed there.

For the **blastp** tool we need to specify the database(s), the query
sequence in FASTA format (although the server is forgiving, and also
accepts plain text without the proper FASTA header), the E-value cutoff
and the output format. We encode the data into JSON and send this as
the body of the request.

In the [Python code](../static/tut4.py) below the task is created by
the POST request. Its URL is defined by the UUID given to the task on creation.

We then loop to check what the status of the task is, polling every second.
We really ought to check whether the task failed, but in this example we don't,
for simplicity.

When the task is finished, we obtain the output by sending a GET request
to the 'output' sub-resource of the task. We write this into
the file [tut4_output.txt](../static/tut4_output.txt).


    # tut4: Create a task using blastp, and wait until finished.

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


Deleting a task
---------------

A task is persistent. It remains on the server until it is explicitly deleted.
This [Python code](../static/tut5.py) shows how a task can be deleted.
The URL of the task must be known in order to delete it.

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

The response for the DELETE request is a HTTP Redirect to the list of 
tasks for the account owning the deleted task.

