""" Adhoc web resource: simple bioinformatics tasks.

Unit tests for the web resource API.
"""

import unittest
import optparse
import httplib
import wsgiref.headers
import base64
import json
import urllib
import urlparse
import time

configuration = dict(NETLOC = 'localhost',
                     ROOT = '/adhoc',
                     ACCOUNT = 'test',
                     PASSWORD = 'abc123')


class TestMixin(object):

    def get_connection(self):
        try:
            host, port = configuration['NETLOC'].split(':', 1)
        except ValueError:
            host = configuration['NETLOC']
            port = None
        return httplib.HTTPConnection(host, port)

    def get_path(self, path_or_url):
        parts = urlparse.urlparse(path_or_url)
        if parts.scheme:
            self.assertEqual(parts.scheme, 'http')
            self.assertEqual(parts.netloc, configuration['NETLOC'])
        if parts.path.startswith(configuration['ROOT']):
            return parts.path[len(configuration['ROOT']):]
        else:
            return parts.path

    def get_headers(self, accept='application/json', **hdrs):
        headers = wsgiref.headers.Headers([(k.replace('_', '-'), v)
                                           for k,v in hdrs.items()])
        encoded = base64.b64encode("%s:%s" % (configuration['ACCOUNT'],
                                              configuration['PASSWORD']))
        auth = "Basic %s" % encoded
        headers.add_header('Authorization', auth)
        headers.add_header('Accept', accept)
        return dict(headers.items())

    def GET(self, resource, accept='application/json', **query):
        cnx = self.get_connection()
        urlpath = configuration['ROOT'] + resource
        if query:
            urlpath += '?' + urllib.urlencode(query)
        cnx.request('GET', urlpath,
                    headers=self.get_headers(accept=accept))
        return cnx.getresponse()

    def POST(self, resource, accept='application/json', outdata=None):
        cnx = self.get_connection()
        urlpath = configuration['ROOT'] + resource
        if outdata:
            cnx.request('POST', urlpath,
                        body=json.dumps(outdata),
                        headers=self.get_headers(accept=accept,
                                                 content_type='application/json'))
        else:
            cnx.request('POST', urlpath,
                        headers=self.get_headers(accept=accept))
        return cnx.getresponse()

    def DELETE(self, resource):
        cnx = self.get_connection()
        urlpath = configuration['ROOT'] + resource
        cnx.request('DELETE', urlpath, headers=self.get_headers())
        return cnx.getresponse()


class TestAccess(TestMixin, unittest.TestCase):
    "Check basic access."

    def test_GET_home_HTML(self):
        "Fetch the home page, in HTML format."
        response = self.GET('/', accept='text/html')
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        headers = wsgiref.headers.Headers(response.getheaders())
        self.assert_(headers.get('content-type').startswith('text/html'))

    def test_GET_home_JSON(self):
        "Fetch the home page, in JSON format."
        response = self.GET('/')
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        headers = wsgiref.headers.Headers(response.getheaders())
        self.assert_(headers.get('content-type') == 'application/json')
        try:
            data = json.loads(response.read())
        except ValueError:
            self.fail('invalid JSON data')

    def test_GET_home_XYZ(self):
        "Try fetching the home page in an impossible format."
        response = self.GET('/', accept='text/xyz')
        self.assertEqual(response.status, httplib.NOT_ACCEPTABLE,
                         msg="HTTP status %s" % response.status)

    def test_GET_nonexistent(self):
        "Try fetching a non-existent resource."
        response = self.GET('/doesnotexist')
        self.assertEqual(response.status, httplib.NOT_FOUND,
                         msg="HTTP status %s" % response.status)


class TestAccount(TestMixin, unittest.TestCase):
    "Test account handling."

    def test_GET_accounts(self):
        "Try fetching accounts list for non-admin test user."
        response = self.GET('/accounts')
        self.assertEqual(response.status, httplib.FORBIDDEN,
                         msg="HTTP status %s" % response.status)

    def test_GET_account(self):
        "Fetch the data for this account, in JSON format."
        response = self.GET("/account/%s" % configuration['ACCOUNT'])
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        headers = wsgiref.headers.Headers(response.getheaders())
        self.assert_(headers.get('content-type') == 'application/json')
        try:
            data = json.loads(response.read())
        except ValueError:
            self.fail('invalid JSON data')

    def test_GET_account_admin(self):
        "Try fetching 'admin' account data."
        response = self.GET('/account/admin')
        self.assertEqual(response.status, httplib.FORBIDDEN,
                         msg="HTTP status %s" % response.status)


class TestBlastp(TestMixin, unittest.TestCase):
    "Test creating and executing a blastp task."

    def test_GET_blastp(self):
        "Get the data for blastp tool."
        response = self.GET('/blastp')
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        try:
            data = json.loads(response.read())
        except ValueError:
            self.fail('invalid JSON data')

    def test_POST_blastp(self):
        "Create, execute and delete a task based on data for the tool."
        response = self.GET('/blastp')
        try:
            data = json.loads(response.read())
        except ValueError:
            self.fail('invalid JSON data')
        tool = data.get('tool')
        self.assert_(tool is not None)
        self.assertEqual(tool['name'],'blastp')
        fields = tool.get('fields')
        self.assert_(fields is not None)
        lookup = dict([(f['name'], f) for f in fields])
        db = None
        size = -1
        db = lookup.get('db')
        self.assert_(db is not None)
        dbs = [c['value'] for c in db['options']]
        self.assert_(len(dbs) > 0)
        outdata = dict(title='unittest',
                       db=dbs,
                       task_type='blastp-short',
                       query_content='>test\nQEEYSAMRDQYMRTGEGFLCVFAINNTKSFEDIHQYREQIKRVKDSDDVPMVLVGNKCDL',
                       evalue=10.0,
                       outfmt=0)
        response = self.POST('/blastp', outdata=outdata)
        self.assertEqual(response.status, httplib.SEE_OTHER,
                         msg="HTTP status %s" % response.status)
        url = response.getheader('location')
        self.assert_(url)
        path = self.get_path(url)
        # Loop until task is finished
        for waiting in range(0, 10):
            time.sleep(1.0)
            response = self.GET(path + '/status')
            self.assertEqual(response.status, httplib.OK,
                             msg="HTTP status %s" % response.status)
            status = response.read()
            if status in ['finished', 'failed', 'stopped']: break
        else:
            self.fail('too long execution time')
            return
        self.assertEqual(status, 'finished')
        # Cleanup
        response = self.GET(path)
        data = json.loads(response.read())
        response = self.DELETE("/task/%s" % data['task']['iui'])
        self.assertEqual(response.status, httplib.SEE_OTHER,
                         msg="HTTP status %s" % response.status)


def parse_command_line():
    parser = optparse.OptionParser()
    parser.add_option('--account', '-a', action='store',
                      default=configuration['ACCOUNT'])
    parser.add_option('--password', '-p', action='store')
    url = urlparse.urlunsplit(('http',
                               configuration['NETLOC'],
                               configuration['ROOT'],
                               '',
                               ''))
    parser.add_option('--url', '-u', action='store', default=url)
    options, arguments = parser.parse_args()
    if options.url:
        parts = urlparse.urlsplit(options.url)
        if parts.scheme != 'http':
            raise ValueError("no support for '%s' scheme" % parts.scheme)
        configuration['NETLOC'] = parts.netloc
        configuration['ROOT'] = parts.path
    if options.account:
        configuration['ACCOUNT'] = options.account
    if options.password:
        configuration['PASSWORD'] = options.password


if __name__ == '__main__':
    parse_command_line()
    suites = []
    for klass in [TestAccess,
                  TestAccount,
                  TestBlastp]:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(klass))
    alltests = unittest.TestSuite(suites)
    print "Testing http://%s/%s ...\n" % (configuration['NETLOC'],
                                          configuration['ROOT'])
    unittest.TextTestRunner(verbosity=2).run(alltests)
