""" Adhoc: Simple web application for task execution.

Unit tests for the web resource API.
"""

import time
import httplib

from wrapid.testbase import *


URL = 'http://localhost/adhoc'
ACCOUNT = 'test'
PASSWORD = 'abc123'


class TestAccess(TestBase):
    "Check basic access."

    def test_GET_home_HTML(self):
        "Fetch the home page, in HTML format."
        wr = self.get_wr('text/html')
        response = wr.GET('/')
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        headers = self.get_headers(response)
        self.assert_(headers.get('content-type').startswith('text/html'))

    def test_GET_home_JSON(self):
        "Fetch the home page, in JSON format."
        response = self.wr.GET('/')
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        headers = self.get_headers(response)
        self.assert_(headers['content-type'] == 'application/json',
                     msg=headers['content-type'])
        self.get_json_data(response)

    def test_GET_home_TXT(self):
        "Fetch the home page, in TXT pprint format."
        wr = self.get_wr('text/plain')
        response = wr.GET('/')
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        headers = self.get_headers(response)
        self.assert_(headers['content-type'].startswith('text/plain'),
                     msg=headers['content-type'])
        data = self.get_txt_data(response)
        self.assert_(data is not None, msg='data has non-None content')

    def test_GET_home_NOSUCH(self):
        "Try fetching the home page in an impossible format."
        wr = self.get_wr('text/nosuch')
        response = wr.GET('/')
        self.assertEqual(response.status, httplib.NOT_ACCEPTABLE,
                         msg="HTTP status %s" % response.status)

    def test_GET_nonexistent(self):
        "Try fetching a non-existent resource."
        response = self.wr.GET('/doesnotexist')
        self.assertEqual(response.status, httplib.NOT_FOUND,
                         msg="HTTP status %s" % response.status)

    def test_login(self):
        "Check explicit login."
        response = self.wr.GET('/login')
        self.assertEqual(response.status, httplib.SEE_OTHER,
                         msg="HTTP status %s" % response.status)


class TestAccount(TestBase):
    "Test account handling."

    def test_GET_accounts(self):
        "Try fetching accounts list for non-admin test user."
        response = self.wr.GET('/accounts')
        self.assertEqual(response.status, httplib.FORBIDDEN,
                         msg="HTTP status %s" % response.status)

    def test_GET_account(self):
        "Fetch the data for this account, in JSON format."
        response = self.wr.GET("/account/%s" % self.wr.account)
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        headers = self.get_headers(response)
        self.assert_(headers['content-type'] == 'application/json',
                     msg=headers['content-type'])
        self.get_json_data(response)

    def test_GET_account_admin(self):
        "Try fetching 'admin' account data."
        response = self.wr.GET('/account/admin')
        self.assertEqual(response.status, httplib.FORBIDDEN,
                         msg="HTTP status %s" % response.status)


class TestBlastp(TestBase):
    "Test creating and executing a blastp task."

    def test_GET_blastp(self):
        "Get the data for blastp tool."
        response = self.wr.GET('/blastp')
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        self.get_json_data(response)

    def test_POST_blastp(self):
        "Create, execute and delete a task based on data for the blastp tool."
        response = self.wr.GET('/blastp')
        data = self.get_json_data(response)
        form = data.get('form')
        self.assert_(form is not None)
        self.assertEqual(form['tool'], 'blastp')
        fields = form.get('fields')
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
        data = dict(title='unittest',
                    db=smallest['value'],
                    task_type='blastp-short',
                    query_content='>test\nQEEYSAMRDQYMRTGEGFLCVFAINNTKSFEDIHQYREQIKRVKDSDDVPMVLVGNKCDL',
                    evalue=10.0,
                    outfmt=0)
        response = self.wr.POST('/blastp', data=data)
        self.assertEqual(response.status, httplib.SEE_OTHER,
                         msg="HTTP status %s" % response.status)
        headers = self.get_headers(response)
        url = headers['location']
        self.assert_(url)
        path = self.wr.get_rpath(url)
        # Loop until task is finished
        for waiting in range(0, 10):
            time.sleep(1.0)
            response = self.wr.GET(path + '/status')
            self.assertEqual(response.status, httplib.OK,
                             msg="HTTP status %s" % response.status)
            status = response.read()
            if status in ['finished', 'failed', 'stopped']: break
        else:
            self.fail('too long execution time')
            return
        self.assertEqual(status, 'finished')
        # Check result
        response = self.wr.GET(path)
        data = self.get_json_data(response)
        # Cleanup
        response = self.wr.DELETE("/task/%s" % data['task']['iui'])
        self.assertEqual(response.status, httplib.SEE_OTHER,
                         msg="HTTP status %s" % response.status)

class TestBlastn(TestBase):
    "Test creating and executing a blastn task."

    def test_POST_blastn(self):
        """Create, execute and delete a task based on data for the blastn tool.
        Try pure sequence input data, and specify XML output."""
        response = self.wr.GET('/blastn')
        data = self.get_json_data(response)
        form = data.get('form')
        self.assert_(form is not None)
        self.assertEqual(form['tool'], 'blastn')
        fields = form.get('fields')
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
        data = dict(title='unittest',
                    db=smallest['value'],
                    task_type='blastn-short',
                    query_content='CGATGCTAGCTAGCGCGCTAGATCGAGCTCTGATAGCTAGCTG',
                    evalue=10.0,
                    outfmt=5)
        response = self.wr.POST('/blastn', data=data)
        self.assertEqual(response.status, httplib.SEE_OTHER,
                         msg="HTTP status %s" % response.status)
        headers = self.get_headers(response)
        url = headers['location']
        self.assert_(url)
        path = self.wr.get_rpath(url)
        # Loop until task is finished
        for waiting in range(0, 10):
            time.sleep(1.0)
            response = self.wr.GET(path + '/status')
            self.assertEqual(response.status, httplib.OK,
                             msg="HTTP status %s" % response.status)
            status = response.read()
            if status in ['finished', 'failed', 'stopped']: break
        else:
            self.fail('too long execution time')
            return
        self.assertEqual(status, 'finished')
        # Check output
        response = self.wr.GET(path + '/output')
        data = self.get_xml_data(response)
        # Cleanup
        response = self.wr.DELETE(path)
        self.assertEqual(response.status, httplib.SEE_OTHER,
                         msg="HTTP status %s" % response.status)


if __name__ == '__main__':
    ex = TestExecutor(url=URL, account=ACCOUNT, password=PASSWORD)
    print 'Testing', ex.wr
    ex.test(TestAccess,
            TestAccount,
            TestBlastp,
            TestBlastn)
