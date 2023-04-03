import logging
import os
import re
import unittest

import sys
if sys.version_info >= (3, 3):
    from unittest.mock import patch
else:
    from mock import patch

from oc_cdtapi.DmsAPI import DmsAPI

import json

class FakeJson(object):
    def __init__(self):
        self.response = None

    def setresp(self, resp):
        self.response = resp

    def json(self):
        return self.response

class _Response(object):
    """
    Fake response object
    """

    def __init__(self, data):
        self.content = data
        self.status_code = 200

    def json(self):
        return json.loads(self.content)


class _Session(object):
    """
    Fake requests session
    """

    def __init__(self, handler):
        self.handler = handler

    def get(self, req, params = None, **other):
        r = req
        if params is not None and len(params) > 0: 
            r += '?' + '&'.join(map(lambda x,y: x+'='+y, list(params.items()))) # this makes from params dict a URL string
            return _Response(self.handler(r))
        else:
            components_json = FakeJson()
            components_json.setresp({"components":[{"id":"appserver"}]})
            return components_json


class _DmsAPI(DmsAPI):

    def __init__(self, *args, **argv):
        super(_DmsAPI, self).__init__(*args, **argv) # calling constructor in DmsAPI
        self.web = _Session(self._read_url) # here we redefine real requests session with fake one


    def get(self, url, params = None, headers = None, verify=False):
        req_a = '/'.join(url)
        if re.match('.+\/component\/.+\/version\/.+\/distribution\/.+\/gav$',req_a) and params: req_a = req_a + '.some'
        data = self._read_url(req_a)
        resp = FakeJson()
        resp.setresp(json.loads(data))
        return resp


    def _read_url(self,url):
        """
        override http request method
        """
        if re.match('.+\/component\/.+\/versions',url):
            return '{"versions":[{"version":"1.7.796","status":"RELEASE","versionInfo":{"snapshot":false,"rcVersion":false,"major":2,"minor":0,"service":1950,"itemsCount":4,"fix":0,"buildNumber":0}}]}'
        elif re.match('.+\/component\/.+\/version\/.+\/distribution\/list$',url):
            return '[{"name":"appserver","classifier":"rhel6-linux-x64"},{"name":"appserver","classifier":"rhel7-linux-x64"}]'
        elif re.match('.+\/component\/.+\/version\/.+\/distribution\/.+\/gav.+$',url):
            return '{"groupId":"com.localhost.distribution.appserver","artifactId":"appserver","version":"1.7.796","classifier":"windows-x64","packaging":"zip"}'
        elif re.match('.+\/component\/.+\/version\/.+\/distribution\/.+\/gav$',url):
            return '{"groupId":"com.localhost.distribution.appserver","artifactId":"appserver","version":"1.7.796","packaging":"zip"}'
        return '[]'



class TestDmsAPI(unittest.TestCase):


#    def test_dms(self):
#        """
#        Test if dms is properly configured and alive
#        """
#        da = _DmsAPI()
#        data = da.ping_dms()
#        self.assertRegexpMatches(data, '.+links+')
#
    @patch.dict(os.environ, {"DMS_URL": "file://dev/null/","DMS_TOKEN": "some-hashed-value", "DMS_CRS_URL": "file://dev/null/"})
    def setUp(self):
        self.dms_api = _DmsAPI()

    def test_get_components(self):
        test_ok = False
        all_c = self.dms_api.get_components()
        if {'id': 'appserver'} in all_c:
            test_ok = True
        self.assertTrue(test_ok)


    def test_get_versions(self):
        test_ok = False
        component = 'appserver'
        all_v = self.dms_api.get_versions(component)
        if '1.7.796' in all_v:
            test_ok = True
        self.assertTrue(test_ok)


    def test_get_types(self):
        test_ok = False
        all_t = self.dms_api.get_types()
        if 'distribution' in all_t:
            test_ok = True
        self.assertTrue(test_ok)


    def test_get_artifacts(self):
        test_ok = False
        component = 'appserver'
        ctype = 'distribution'
        version = '1.7.796'
        all_a = self.dms_api.get_artifacts(component, version, ctype)
        for a in all_a:
            if a['name'] == 'appserver':
                test_ok = True
        self.assertTrue(test_ok)


    def test_get_gav_no_classifier(self):
        test_ok = False
        component = 'appserver'
        ctype = 'distribution'
        version = '1.7.796'
        artifact = 'appserver'
        classifier = None
        gav = self.dms_api.get_gav(component, version, 'distribution', artifact, classifier)
        self.assertEqual(gav,'com.localhost.distribution.appserver:appserver:1.7.796:zip')


    def test_get_gav_classifier(self):
        test_ok = False
        component = 'appserver'
        ctype = 'distribution'
        version = '1.7.796'
        artifact = 'appserver'
        classifier = 'windows-x64'
        gav = self.dms_api.get_gav(component, version, 'distribution', artifact, classifier)
        self.assertEqual(gav,'com.localhost.distribution.appserver:appserver:1.7.796:zip:windows-x64')



if __name__ == '__main__':
    unittest.main()
