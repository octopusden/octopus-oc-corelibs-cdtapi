import logging, unittest
from oc_cdtapi.DmsGetverAPI import DmsGetverAPI



class _DmsGetverAPI (DmsGetverAPI):


    def __init__ (self):
        super (_DmsGetverAPI, self).__init__ ('fake url', 'fake user', 'fake password')
        self.req_counter = 0


    def _fake_state_info (self, distr_id = None, distr_state = None, distr_filename = None):
        distr_state_info = {}
        distr_state_info ['id'] = distr_id
        distr_state_info ['state'] = distr_state
        distr_state_info ['fileName'] = distr_filename
        return distr_state_info


    def _fake_state_info_diff (self, distr_id = None, distr_state = None, distr_filename = None):
        distr_state_info = {}
        distr_state_info ['id'] = distr_id
        distr_state_info ['state'] = distr_state
        distr_state_info ['fileName'] = distr_filename
        distr_state_info ['initialFilters'] = 'FILTER'
        distr_state_info ['targetFilters'] = 'FILTER'
        distr_state_info ['initialVersion'] = 'VERSION'
        distr_state_info ['targetVersion'] = 'VERSION'
        return distr_state_info


    def _fake_gav (self):
        fake_gav = {}
        fake_gav ['groupId'] = 'groupId'
        fake_gav ['artifactId'] = 'artifactId'
        fake_gav ['version'] = 'version'
        fake_gav ['packaging'] = 'packaging'
        return fake_gav


    def get (self, url, params=None):
        resp = FakeResp ()
        if (url == 'dms-getver/rest/api/1/distribution' and params and params.get('version') == '09.99.99.99') or \
           url == 'dms-getver/rest/api/1/distribution/id:99' or \
           url == 'dms-getver/rest/api/1/distribution-difference/id:99':
            if self.req_counter == 0:
                resp.status_code = 200
                resp.content = None
                resp.jdata = self._fake_state_info (99, 'PROCESSING', None)
                self.req_counter += 1
            else:
                resp.status_code = 200
                resp.content = None
                resp.jdata = self._fake_state_info (99, 'READY', None)
                self.req_counter += 1
        elif url == 'dms-getver/rest/api/1/distribution-difference':
            resp.status_code = 200
            resp.content = None
            resp.jdata = self._fake_state_info_diff (99, 'PROCESSING', None)
        elif (url == 'dms-getver/rest/api/1/distribution' and params and params.get('version') == '07.77.77.77'):
            resp.status_code = 404
            jdata = {}
            jdata ['code'] = 'DMS-GETVER-40001'
            resp.jdata = jdata
        elif url == 'dms-getver/distribution/id:99/download':
            if self.req_counter < 3:
                resp.status_code = 200
                resp.content = 'ABCDEF0123456789'
                resp.jdata = self._fake_state_info (99, 'READY', None)
            else:
                resp.status_code = 404
                resp.content = None
                resp.jdata = None
        elif url == 'dms-getver/distribution/id:88/download':
            resp.status_code = 200
            resp.jdata = self._fake_state_info (99, 'PROCESSING', None)
        elif url == 'dms-getver/distribution/id:77/download':
            resp.status_code = 404
            resp.jdata = None
        elif url == 'dms-getver/rest/api/1/distribution/id:99/gav':
            resp.status_code = 200
            resp.jdata = self._fake_gav ()
        elif url.find ('/log') != -1:
            if url.find ('99') != -1:
                resp.status_code = 200
                resp.text = 'dms log data'
            else:
                resp.status_code = 404
                resp.text = 'log not found'
        return resp


    def post (self, url, json = None):
        resp = FakeResp ()
        if url == 'dms-getver/rest/api/1/distribution' or \
           url == 'dms-getver/rest/api/1/distribution-difference':
            if 'version' in json.keys ():
                version = json ['version']
            elif 'targetVersion' in json.keys ():
                version = json ['targetVersion']
            if version == '09.99.99.99':
                resp.status_code = 200
                resp.content = None
                resp.jdata = self._fake_state_info (99, 'INITIATED', None)
            elif version == '08.88.88.88':
                resp.status_code = 500
                resp.content = None
        return resp




class FakeResp (object):


    def __init__ (self):
        self.jdata = None


    def status_code (self):
        return None


    def content (self):
        return None


    def json (self):
        if self.jdata:
            return self.jdata
        else:
            raise ValueError


    def text (self):
        return None




class TestDmsGetverAPI (unittest.TestCase):


    def test_none (self):
        self.assertTrue (True)


    def test_dms_log_ok (self):
        da = _DmsGetverAPI ()
        distr_option = 'full'
        log = da.get_dms_log (99, distr_option)
        self.assertEqual (log, 'dms log data')


    def test_dms_log_404 (self):
        da = _DmsGetverAPI ()
        distr_option = 'full'
        log = da.get_dms_log (77, distr_option)
        self.assertIsNone (log)


    def test_create_distr_request_full (self):
        da = _DmsGetverAPI ()
        version = '09.99.99.99'
        distr_type = 'CARDS'
        client_filter = 'FILTER'
        distr_state_info = da.create_distr_request (version = version, distr_type = distr_type, client_filter = client_filter)
        state = distr_state_info ['state']
        self.assertEqual (state, 'INITIATED')


    def test_create_distr_request_diff (self):
        da = _DmsGetverAPI ()
        source_version = '08.88.88.88'
        version = '09.99.99.99'
        distr_type = 'CARDS'
        client_filter = 'FILTER'
        distr_state_info = da.create_distr_request (version = version, source_version = source_version, distr_type = distr_type, client_filter = client_filter)
        state = distr_state_info ['state']
        self.assertEqual (state, 'INITIATED')


    def test_create_distr_request_filterless (self):
        da = _DmsGetverAPI ()
        source_version = '08.88.88.88'
        version = '09.99.99.99'
        distr_type = 'CARDS'
        client_filter = 'FILTER'
        distr_state_info = da.create_distr_request (version = version, source_version = source_version, distr_type = distr_type, client_filter = None)
        state = distr_state_info ['state']
        self.assertEqual (state, 'INITIATED')


    def test_create_distr_request_500 (self):
        da = _DmsGetverAPI ()
        version = '08.88.88.88'
        distr_type = 'CARDS'
        client_filter = 'FILTER'
        distr_state_info = da.create_distr_request (version = version, distr_type = distr_type, client_filter = None)
        state = distr_state_info ['state']
        self.assertEqual (state, 'HTTP/500')


    def test_dumb_404_dumb0 (self):
        da = _DmsGetverAPI ()
        jdata = {}
        jdata ['code'] = 'DMS-GETVER-40001'
        resp = FakeResp ()
        resp.status_code = 404
        resp.jdata = jdata
        is_dumb = da._dumb_404 (resp)
        self.assertTrue (is_dumb)


    def test_dumb_404_dumb1 (self):
        da = _DmsGetverAPI ()
        jdata = {}
        jdata ['code'] = 'blahblahblah'
        resp = FakeResp ()
        resp.status_code = 404
        resp.jdata = jdata
        is_dumb = da._dumb_404 (resp)
        self.assertFalse (is_dumb)


    def test_dumb_404_real (self):
        da = _DmsGetverAPI ()
        jdata = {}
        resp = FakeResp ()
        resp.status_code = 404
        is_dumb = da._dumb_404 (resp)
        self.assertFalse (is_dumb)


    def test_get_distr_full_ok (self):
        da = _DmsGetverAPI ()
        da.req_counter = 1
        distr_id = 99
        distr_option = 'full'
        distr, distr_state_info = da.get_distr (distr_id, distr_option)
        self.assertEqual (distr, 'ABCDEF0123456789')


    def test_get_distr_full_notready (self):
        da = _DmsGetverAPI ()
        da.req_counter = 1
        distr_id = 88
        distr_option = 'full'
        distr, distr_state_info = da.get_distr (distr_id, distr_option)
        self.assertIsNone (distr)


    def test_get_distr_full_404 (self):
        da = _DmsGetverAPI ()
        da.req_counter = 4
        distr_id = 99
        distr_option = 'full'
        distr, distr_state_info = da.get_distr (distr_id, distr_option)
        self.assertIsNone (distr)


    def test_get_distr_diff_ok (self):
        da = _DmsGetverAPI ()
        da.req_counter = 1
        distr_id = 99
        distr_option = 'diff'
        distr, distr_state_info = da.get_distr (distr_id, distr_option)
        self.assertEqual (distr, 'ABCDEF0123456789')


    def test_get_distr_state_info_full (self):
        da = _DmsGetverAPI ()
        version = '09.99.99.99'
        distr_type = 'CARDS'
        client_filter = 'FILTER'
        distr_state_info = da.get_distr_state_info (version = version, distr_type = distr_type, client_filter = client_filter)
        state = distr_state_info ['state']
        self.assertEqual (state, 'PROCESSING')


    def test_get_distr_state_info_full_dumb404 (self):
        da = _DmsGetverAPI ()
        version = '07.77.77.77'
        distr_type = 'CARDS'
        client_filter = 'FILTER'
        distr_state_info = da.get_distr_state_info (version = version, distr_type = distr_type, client_filter = client_filter)
        state = distr_state_info ['state']
        self.assertEqual (state, 'NOTFOUND')


    def test_get_distr_state_info_diff (self):
        da = _DmsGetverAPI ()
        version = '09.99.99.99'
        source_version = '08.88.88.88'
        distr_type = 'CARDS'
        client_filter = 'FILTER'
        distr_state_info = da.get_distr_state_info (version = version, source_version = source_version, distr_type = distr_type, client_filter = client_filter)
        state = distr_state_info ['state']
        self.assertEqual (state, 'PROCESSING')


    def test_get_distr_state_info_byid_full (self):
        da = _DmsGetverAPI ()
        da.req_counter = 1
        distr_id = 99
        distr_option = 'full'
        distr_state_info = da.get_distr_state_info_byid (distr_id, distr_option)
        state = distr_state_info ['state']
        self.assertEqual (state, 'READY')


    def test_get_distr_state_info_byid_diff (self):
        da = _DmsGetverAPI ()
        da.req_counter = 1
        distr_id = 99
        distr_option = 'diff'
        distr_state_info = da.get_distr_state_info_byid (distr_id, distr_option)
        state = distr_state_info ['state']
        self.assertEqual (state, 'READY')


    def test_get_dms_gav (self):
        da = _DmsGetverAPI ()
        gav = da.get_dms_gav (99, 'full')
        self.assertEqual (gav, 'groupId:artifactId:version:packaging')


    def test_wait_for_state_ok (self):
        da = _DmsGetverAPI ()
        da.wait_state_sleep = 1
        distr_id = 99
        distr_option = 'full'
        distr_state_info = da.wait_for_state (distr_id, distr_option)
        state = distr_state_info ['state']
        self.assertEqual (state, 'READY')


    def test_wait_for_state_timeout (self):
        da = _DmsGetverAPI ()
        da.wait_state_sleep = 5
        da.wait_state_timeout = -1
        distr_id = 99
        distr_option = 'full'
        distr_state_info = da.wait_for_state (distr_id, distr_option)
        state = distr_state_info ['state']
        self.assertEqual (state, 'TIMEOUT')


if __name__ == '__main__':
    unittest.main()

