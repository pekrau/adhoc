""" Adhoc web resource: simple bioinformatics tasks.

Unit tests for the web resource API.
"""

import time

from wrapid.testbase import *


class TestAccess(TestBase):
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


class TestAccount(TestBase):
    "Test account handling."

    def test_GET_accounts(self):
        "Try fetching accounts list for non-admin test user."
        response = self.GET('/accounts')
        self.assertEqual(response.status, httplib.FORBIDDEN,
                         msg="HTTP status %s" % response.status)

    def test_GET_account(self):
        "Fetch the data for this account, in JSON format."
        response = self.GET("/account/%s" % self.configuration.account)
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


class TestBlastp(TestBase):
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
        self.assertEqual(tool['name'], 'blastp')
        fields = tool.get('fields')
        self.assert_(fields is not None)
        lookup = dict([(f['name'], f) for f in fields])
        db = None
        size = -1
        db = lookup.get('db')
        self.assert_(db is not None)
        # Select the smallest database
        smallest = db['options'][0]
        for database in db['options'][1:]:
            if database['size'] < smallest['size']:
                smallest = database
        self.assert_(smallest is not None)
        outdata = dict(title='unittest',
                       db=smallest['value'],
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


if __name__ == '__main__':
    from adhoc import configuration
    ex = TestExecutor(root=configuration.TEST_ROOT,
                      account=configuration.TEST_ACCOUNT,
                      password=configuration.TEST_PASSWORD)
    print "Testing http://%s/%s ...\n" % (ex.netloc, ex.root)
    ex.test(TestAccess,
            TestAccount,
            TestBlastp)
