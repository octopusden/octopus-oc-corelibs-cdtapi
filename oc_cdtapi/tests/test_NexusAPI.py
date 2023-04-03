from unittest import TestCase
from oc_cdtapi import NexusAPI
from sys import version_info

if version_info.major == 2:
    import mock
else:
    from unittest import mock

import posixpath
import os
import tempfile
import re

from .mocks.NexusAPILsMock import NexusAPILsMock

import logging
logging.getLogger().propagate = False
logging.getLogger().disabled = True

_nexus_url = "http://127.0.0.1:8081/nexus"

class NexusAPITestSuite(TestCase):

    @mock.patch.dict("os.environ", {"MVN_URL": _nexus_url})
    @mock.patch('requests.Session')
    def setUp(self, session_mock):
        self.assertEqual(os.getenv("MVN_URL"), _nexus_url)
        self.api = NexusAPI.NexusAPI()
        self.assertIsInstance(self.api.web, mock.MagicMock)
        self.assertFalse(self.api.is_artifactory)
        self.assertTrue(self.api.is_nexus)
        self.put_headers = {'Content-Type': 'application/binary'}

    def test_init_bare(self):
        self.assertEqual(self.api.root.strip(posixpath.sep), _nexus_url.strip(posixpath.sep))

    @mock.patch.dict("os.environ", {"MVN_URL": _nexus_url})
    @mock.patch('requests.Session')
    def test_init_parms(self, session):
        _api = NexusAPI.NexusAPI(root=_nexus_url, 
                user="user",
                auth="password",
                upload_repo="upload",
                download_repo="download")

        self.assertEqual(_api.root.strip(posixpath.sep), _nexus_url.strip(posixpath.sep))
        self.assertEqual(_api.web.auth[0], "user")
        self.assertEqual(_api.web.auth[1], "password")

        # since __download_repo and __upload_repo are hidden from us
        _expected_put = posixpath.join(_nexus_url, "content", "repositories", "upload", NexusAPI.gav_to_path("g:a:v"))
        _retval_put = mock.MagicMock()
        _retval_put.status_code = 200
        _api.web.put = mock.MagicMock(return_value=_retval_put)
        _api.upload('g:a:v', data='test_data')

        _expected_get = posixpath.join(_nexus_url, "content", "repositories", "download", NexusAPI.gav_to_path("g:a:v"))
        _retval_get = mock.MagicMock()
        _retval_get.status_code = 200
        _retval_get.data = b"test_data"
        _api.web.get = mock.MagicMock(return_value=_retval_get)
        _api.cat('g:a:v')

        # urllib.urlparse.urljoin is not suitable for us since it joins only host part + relative part
        _api.web.put.assert_called_once_with(_expected_put, data='test_data', files=None, headers=self.put_headers, params=None)
        _api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=None, stream=False)

    def test_cat_general(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = b"test_response"
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _res = self.api.cat("g:a:v:p:c")
        _expected_get = posixpath.join(_nexus_url, "content", "repositories", "public", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=None, stream=False)
        self.assertEqual(_res, "test_response")

    @mock.patch.dict("os.environ", {"MVN_URL": _nexus_url, "MVN_DOWNLOAD_REPO": "download"})
    def test_cat_env(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = b"test_response"
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _res = self.api.cat("g:a:v:p:c")
        _expected_get = posixpath.join(_nexus_url, "content", "repositories", "download", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=None, stream=False)
        self.assertEqual(_res, "test_response")

    def test_cat_repo(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = b"test_response"
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _res = self.api.cat("g:a:v:p:c", repo="download")
        _expected_get = posixpath.join(_nexus_url, "content", "repositories", "download", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=None, stream=False)
        self.assertEqual(_res, "test_response")

    def test_cat_codepage(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = b"test_response_rus_\xf2\xe5\xf1\xf2\xee\xe2\xe0\xff_\xf5\xf0\xe5\xed\xfc"
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _res = self.api.cat("g:a:v:p:c", encoding="cp1251")
        _expected_get = posixpath.join(_nexus_url, "content", "repositories", "public", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=None, stream=False)
        self.assertEqual(_res, b"test_response_rus_\xf2\xe5\xf1\xf2\xee\xe2\xe0\xff_\xf5\xf0\xe5\xed\xfc".decode("cp1251"))

    def test_cat_binary(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = b"test_response_bin"
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _res = self.api.cat("g:a:v:p:c", binary=True)
        _expected_get = posixpath.join(_nexus_url, "content", "repositories", "public", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=None, stream=False)
        self.assertEqual(_res, b"test_response_bin")

    def test_cat_response(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = b"test_response_bin"
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _res = self.api.cat("g:a:v:p:c", response=True)
        _expected_get = posixpath.join(_nexus_url, "content", "repositories", "public", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=None, stream=False)
        self.assertEqual(_res, _ret)

    def test_cat_rest_call(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = b"test_response"
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _res = self.api.cat("g:a:latest:p:c", rest_call=True)
        _expected_get = posixpath.join(_nexus_url, 'service', 'local', 'artifact', 'maven', 'content')
        _expected_params = {'r': "public", 'g': 'g', 'a': 'a', 'v': 'latest', 'p': 'p', 'c': 'c'}
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=_expected_params, stream=False)
        self.assertEqual(_res, "test_response")

    def test_cat_write_to(self):
        _flt = tempfile.NamedTemporaryFile()
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = b"test_response_write"
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _res = self.api.cat("g:a:v:p:c", write_to=_flt.name)
        _expected_get = posixpath.join(_nexus_url, "content", "repositories", "public", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=None, stream=False)
        self.assertEqual(_res, _ret)
        _flt.seek(0, 0)
        self.assertEqual(b"test_response_write", _flt.read())

    def test_cat_rest_write_to(self):
        _flt = tempfile.NamedTemporaryFile()
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = b"test_response_write_rest_bin"
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _res = self.api.cat("g:a:latest:p:c", rest_call=True, write_to=_flt.name)
        _expected_get = posixpath.join(_nexus_url, 'service', 'local', 'artifact', 'maven', 'content')
        _expected_params = {'r': "public", 'g': 'g', 'a': 'a', 'v': 'latest', 'p': 'p', 'c': 'c'}
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=_expected_params, stream=False)
        self.assertEqual(_res, _ret)
        _flt.seek(0, 0)
        self.assertEqual(b"test_response_write_rest_bin", _flt.read())

    def test_cat_encoding_error(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = b"test_response_rus_\xf2\xe5\xf1\xf2\xee\xe2\xe0\xff_\xf5\xf0\xe5\xed\xfc"
        # this is cp1251 legal string, but incorrect for utf-8
        self.api.web.get = mock.MagicMock(return_value=_ret)

        _res = None
        with self.assertRaises(UnicodeDecodeError):
            _res = self.api.cat("g:a:v:p:c", encoding="utf-8", enc_errors='strict')

        _expected_get = posixpath.join(_nexus_url, "content", "repositories", "public", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=None, stream=False)
        self.assertIsNone(_res)

    def test_cat_exception(self):
        _ret = mock.MagicMock()
        _ret.status_code = 404
        self.api.web.get = mock.MagicMock(return_value=_ret)

        with self.assertRaises(NexusAPI.NexusAPIError):
            _res = self.api.cat("g:a:v:p:c")

        _expected_get = posixpath.join(_nexus_url, "content", "repositories", "public", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=None, stream=False)

    def test_exists_general(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.head = mock.MagicMock(return_value=_ret)
        _expected_head = posixpath.join(_nexus_url, "content", "repositories", "public", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.assertTrue(self.api.exists("g:a:v:p:c"))
        self.api.web.head.assert_called_once_with(_expected_head, params=None, files=None, data=None, headers=None)
        self.api.web.get.assert_not_called()

    def test_exists_repo(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.head = mock.MagicMock(return_value=_ret)
        _repo = 'some_repo'
        _expected_head = posixpath.join(_nexus_url, "content", "repositories", _repo, NexusAPI.gav_to_path("g:a:v:p:c"))
        self.assertTrue(self.api.exists("g:a:v:p:c", repo=_repo))
        self.api.web.head.assert_called_once_with(_expected_head, params=None, files=None, data=None, headers=None)
        self.api.web.get.assert_not_called()

    @mock.patch.dict("os.environ", {"MVN_URL": _nexus_url, "MVN_DOWNLOAD_REPO": "download"})
    def test_exists_env(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.head = mock.MagicMock(return_value=_ret)
        _repo = 'download'
        _expected_head = posixpath.join(_nexus_url, "content", "repositories", _repo, NexusAPI.gav_to_path("g:a:v:p:c"))
        self.assertTrue(self.api.exists("g:a:v:p:c"))
        self.api.web.head.assert_called_once_with(_expected_head, params=None, files=None, data=None, headers=None)
        self.api.web.get.assert_not_called()

    def test_exists_rest(self):
        _ret = mock.MagicMock()
        _ret.status_code = 307
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _expected_get = posixpath.join(_nexus_url, 'service', 'local', 'artifact', 'maven', 'redirect')
        _expected_parms = {'g': 'g', 'a': 'a', "v": 'v', "p": 'p', 'c': 'c', 'r': "public"}
        self.assertTrue(self.api.exists("g:a:v:p:c", rest_call=True))
        self.api.web.head.assert_not_called()
        self.api.web.get.assert_called_once_with(_expected_get, allow_redirects=False, params=_expected_parms, files=None, data=None, headers=None)

    def test_not_exists_general(self):
        _ret = mock.MagicMock()
        _ret.status_code = 404
        self.api.web.head = mock.MagicMock(return_value=_ret)
        _expected_head = posixpath.join(_nexus_url, "content", "repositories", "public", NexusAPI.gav_to_path("g:a:v:p:c"))
        self.assertFalse(self.api.exists("g:a:v:p:c"))
        self.api.web.head.assert_called_once_with(_expected_head, params=None, files=None, data=None, headers=None)
        self.api.web.get.assert_not_called()

    def test_not_exists_repo(self):
        _ret = mock.MagicMock()
        _ret.status_code = 404
        self.api.web.head = mock.MagicMock(return_value=_ret)
        _repo = 'some_repo'
        _expected_head = posixpath.join(_nexus_url, "content", "repositories", _repo, NexusAPI.gav_to_path("g:a:v:p:c"))
        self.assertFalse(self.api.exists("g:a:v:p:c", repo=_repo))
        self.api.web.head.assert_called_once_with(_expected_head, params=None, files=None, data=None, headers=None)
        self.api.web.get.assert_not_called()

    @mock.patch.dict("os.environ", {"MVN_URL": _nexus_url, "MVN_DOWNLOAD_REPO": "download"})
    def test_not_exists_env(self):
        _ret = mock.MagicMock()
        _ret.status_code = 404
        self.api.web.head = mock.MagicMock(return_value=_ret)
        _repo = 'download'
        _expected_head = posixpath.join(_nexus_url, "content", "repositories", _repo, NexusAPI.gav_to_path("g:a:v:p:c"))
        self.assertFalse(self.api.exists("g:a:v:p:c"))
        self.api.web.head.assert_called_once_with(_expected_head, params=None, files=None, data=None, headers=None)
        self.api.web.get.assert_not_called()

    def test_not_exists_rest(self):
        _ret = mock.MagicMock()
        _ret.status_code = 404
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _expected_get = posixpath.join(_nexus_url, 'service', 'local', 'artifact', 'maven', 'redirect')
        _expected_parms = {'g': 'g', 'a': 'a', "v": 'v', "p": 'p', 'c': 'c', 'r': "public"}
        self.assertFalse(self.api.exists("g:a:v:p:c", rest_call=True))
        self.api.web.head.assert_not_called()
        self.api.web.get.assert_called_once_with(_expected_get, allow_redirects=False, params=_expected_parms, files=None, data=None, headers=None)

    def test_exists_error(self):
        _ret = mock.MagicMock()
        _ret.status_code = 418
        self.api.web.head = mock.MagicMock(return_value=_ret)
        _expected_head = posixpath.join(_nexus_url, "content", "repositories", "public", NexusAPI.gav_to_path("g:a:v:p:c"))
        with self.assertRaises(NexusAPI.NexusAPIError):
            (self.api.exists("g:a:v:p:c"))

        self.api.web.head.assert_called_once_with(_expected_head, params=None, files=None, data=None, headers=None)
        self.api.web.get.assert_not_called()

    def test_exists_rest_error(self):
        _ret = mock.MagicMock()
        _ret.status_code = 418
        self.api.web.get = mock.MagicMock(return_value=_ret)
        _expected_get = posixpath.join(_nexus_url, 'service', 'local', 'artifact', 'maven', 'redirect')
        _expected_parms = {'g': 'g', 'a': 'a', "v": 'v', "p": 'p', 'c': 'c', 'r': "public"}

        with self.assertRaises(NexusAPI.NexusAPIError):
            (self.api.exists("g:a:v:p:c", rest_call=True))

        self.api.web.head.assert_not_called()
        self.api.web.get.assert_called_once_with(_expected_get, allow_redirects=False, params=_expected_parms, files=None, data=None, headers=None)

    def test_upload_general(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.put = mock.MagicMock(return_value=_ret)
        self.api.update_metadata = mock.MagicMock()
        res = self.api.upload('a.b.c.d:artifact:1.1', repo='repoid', data='HELLO, WORLD!!!', pom = None)
        self.assertEqual(res, _ret)
        _expected_put = posixpath.join(_nexus_url, 'content', 'repositories', 'repoid', 'a', 'b', 'c', 'd', 'artifact', '1.1', 'artifact-1.1.jar')
        self.api.web.put.assert_called_once_with(_expected_put, data='HELLO, WORLD!!!', files=None, headers=self.put_headers, params=None)
        self.api.update_metadata.assert_not_called()

    def test_upload_repo(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.put = mock.MagicMock(return_value=_ret)
        self.api.update_metadata = mock.MagicMock()
        res = self.api.upload('a.b.c.d:artifact:1.1', repo='repositories/id', data='HELLO, WORLD!!!', pom = None)
        self.assertEqual(res, _ret)
        _expected_put = posixpath.join(_nexus_url, 'content', 'repositories', 'id', 'a', 'b', 'c', 'd', 'artifact', '1.1', 'artifact-1.1.jar')
        self.api.web.put.assert_called_once_with(_expected_put, data='HELLO, WORLD!!!', files=None, headers=self.put_headers, params=None)
        self.api.update_metadata.assert_not_called()

    def test_upload_pom(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.put = mock.MagicMock(return_value=_ret)
        self.api.update_metadata = mock.MagicMock()
        res = self.api.upload('a.b.c.d:artifact:1.1','repositories/id','HELLO, WORLD!!!', pom = '<pom>this is a pom</pom>')
        _expected_put = posixpath.join(_nexus_url, 'content', 'repositories', 'id', 'a', 'b', 'c', 'd', 'artifact', '1.1', 'artifact-1.1')
        self.assertEqual(self.api.web.put.call_count, 2)
        self.api.web.put.assert_any_call(_expected_put + '.jar', data='HELLO, WORLD!!!', files=None, headers=self.put_headers, params=None)
        self.api.web.put.assert_any_call(_expected_put + '.pom', data='<pom>this is a pom</pom>', files=None, headers=self.put_headers, params=None)
        self.assertEqual(res, _ret)
        self.api.update_metadata.assert_not_called()

    def test_upload_pom_generate(self):
        _gav = 'a.b.c.d:artifact:1.1:jar:classifier'

        # We do not need to test pom generation here. There are separate tests for it.
        pom_data_expected = NexusAPI.pom_from_gav(_gav)
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.put = mock.MagicMock(return_value=_ret)
        self.api.exists = mock.MagicMock(return_value=False)
        self.api.update_metadata = mock.MagicMock()

        res = self.api.upload(_gav, repo='id', data=b'HELLO, WORLD!!!', pom=True)
        self.assertEqual(res, _ret)
        _expected_exists = NexusAPI.parse_gav(_gav)
        _expected_exists['p'] = 'pom'
        _expected_put = posixpath.join(_nexus_url, 'content', 'repositories', 'id', 'a', 'b', 'c', 'd', 'artifact', '1.1', 'artifact-1.1-classifier')
        self.api.exists.assert_called_once_with(_expected_exists, repo='id')
        self.assertEqual(2, self.api.web.put.call_count)
        self.api.web.put.assert_any_call(_expected_put + '.jar', data=b'HELLO, WORLD!!!', files=None, headers=self.put_headers, params=None)
        self.api.web.put.assert_any_call(_expected_put + '.pom', data=pom_data_expected, files=None, headers=self.put_headers, params=None)
        self.api.update_metadata.assert_not_called()

    def test_upload_pom_generate_with_metadata(self):
        _gav = 'a.b.c.d:artifact:1.1:zip:classifier'
        pom_data_expected = NexusAPI.pom_from_gav(_gav)
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.put = mock.MagicMock(return_value=_ret)
        self.api.exists = mock.MagicMock(return_value=False)
        self.api.update_metadata = mock.MagicMock()

        res = self.api.upload(_gav, repo='id', data=b'HELLO, WORLD!!!', pom=True, metadata=True)
        self.assertEqual(res, _ret)
        _expected_exists = NexusAPI.parse_gav(_gav)
        _expected_exists['p'] = 'pom'
        _expected_put = posixpath.join(_nexus_url, 'content', 'repositories', 'id', 'a', 'b', 'c', 'd', 'artifact', '1.1', 'artifact-1.1-classifier')
        self.api.exists.assert_called_once_with(_expected_exists, repo='id')
        self.assertEqual(2, self.api.web.put.call_count)
        self.api.web.put.assert_any_call(_expected_put + '.zip', data=b'HELLO, WORLD!!!', files=None, headers=self.put_headers, params=None)
        self.api.web.put.assert_any_call(_expected_put + '.pom', data=pom_data_expected, files=None, headers=self.put_headers, params=None)
        self.api.update_metadata.assert_called_once_with('a.b.c.d', 'id')

    def test_upload_pom_exists(self):
        _gav = 'a.b.c.d:artifact:1.1:zip:classifier'
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.put = mock.MagicMock(return_value=_ret)
        self.api.exists = mock.MagicMock(return_value=True)
        self.api.update_metadata = mock.MagicMock()

        res = self.api.upload(_gav, repo='id', data=b'HELLO, WORLD!!!', pom=True)
        self.assertEqual(res, _ret)
        _expected_exists = NexusAPI.parse_gav(_gav)
        _expected_exists['p'] = 'pom'
        _expected_put = posixpath.join(_nexus_url, 'content', 'repositories', 'id', 'a', 'b', 'c', 'd', 'artifact', '1.1', 'artifact-1.1-classifier.zip')
        self.api.exists.assert_called_once_with(_expected_exists, repo='id')
        self.api.web.put.assert_called_once_with(_expected_put, data=b'HELLO, WORLD!!!', files=None, headers=self.put_headers, params=None)
        self.api.update_metadata.assert_not_called()


    def test_updatemeta_general(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.delete = mock.MagicMock(return_value=_ret)

        with self.assertRaises(ValueError):
            self.api.update_metadata()

        self.api.web.delete.assert_not_called()

    @mock.patch.dict("os.environ", {"MVN_URL": _nexus_url, "MVN_UPLOAD_REPO": "upload"})
    def test_updatemeta_general_env(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.delete = mock.MagicMock(return_value=_ret)

        _expected_del = posixpath.join(_nexus_url, "service", "local", "metadata", "repositories", "upload", 'content')
        self.assertEqual(_ret, self.api.update_metadata())
        self.api.web.delete.assert_called_once_with(_expected_del, data=None, files=None, headers=None, params=None)

    def test_updatemeta_repo(self):
        _gav = "a.b.c.d.e.f:aIdS:6.7.8.9.10:puck"
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.delete = mock.MagicMock(return_value=_ret)

        _expected_del = posixpath.join(_nexus_url, "service", "local", "metadata", "repositories", "upload", 'content', NexusAPI.gav_to_path(_gav))
        self.assertEqual(_ret, self.api.update_metadata(gav=_gav, repo='upload'))
        self.api.web.delete.assert_called_once_with(_expected_del, data=None, files=None, headers=None, params=None)

    def test_delete_no_repo(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.delete = mock.MagicMock(return_value=_ret)
        
        with self.assertRaises(ValueError):
            self.api.remove(gav="g:a:v")

        self.api.web.delete.assert_not_called()

    def test_delete_general(self):
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.delete = mock.MagicMock(return_value=_ret)
        _rsp = self.api.remove(repo="repo")

        _del_expected = posixpath.join(_nexus_url, "content", "repositories", "repo")
        self.api.web.delete.assert_called_once_with(_del_expected, data=None, files=None, headers=None, params=None)

    @mock.patch.dict("os.environ", {"MVN_URL": _nexus_url, "MVN_UPLOAD_REPO": "upload"})
    def test_delete_env(self):
        _gav = "g:a:v"
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.delete = mock.MagicMock(return_value=_ret)
        _rsp = self.api.remove(gav=_gav)

        _del_expected = posixpath.join(_nexus_url, "content", "repositories", "upload", NexusAPI.gav_to_path(_gav))
        self.api.web.delete.assert_called_once_with(_del_expected, data=None, files=None, headers=None, params=None)

    def test_delete_repo(self):
        _gav = "g:a:v:p"
        _ret = mock.MagicMock()
        _ret.status_code = 200
        self.api.web.delete = mock.MagicMock(return_value=_ret)
        _rsp = self.api.remove(gav=_gav, repo="idUpload")

        _del_expected = posixpath.join(_nexus_url, "content", "repositories", "idUpload", NexusAPI.gav_to_path(_gav))
        self.api.web.delete.assert_called_once_with(_del_expected, data=None, files=None, headers=None, params=None)

    def test_delete_exc(self):
        _gav = "g:a:v:p:c"
        _ret = mock.MagicMock()
        _ret.status_code = 403
        self.api.web.delete = mock.MagicMock(return_value=_ret)

        with self.assertRaises(NexusAPI.NexusAPIError):
            _rsp = self.api.remove(gav=_gav, repo="idXupload")

        _del_expected = posixpath.join(_nexus_url, "content", "repositories", "idXupload", NexusAPI.gav_to_path(_gav))
        self.api.web.delete.assert_called_once_with(_del_expected, data=None, files=None, headers=None, params=None)


    def test_info_existent(self):
        _resp_xml = """
        <org.sonatype.nexus.rest.model.ArtifactInfoResourceResponse>
            <data>
                <sha1Hash>abcdef123456</sha1Hash>
                <md5Hash>123456abcdef</md5Hash>
                <mimeType>mime-type-g</mimeType>
            </data>
        </org.sonatype.nexus.rest.model.ArtifactInfoResourceResponse>
        """
        _gav = "g:a:v:p"
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = _resp_xml
        self.api.web.get = mock.MagicMock(return_value=_ret)

        self.assertEqual(self.api.info(_gav), {"md5": "123456abcdef", "mime": "mime-type-g"})
        _expected_parms = {"describe": "info"}
        _expected_get = posixpath.join(_nexus_url, "service", "local", "repositories", "public", "content", NexusAPI.gav_to_path(_gav))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=_expected_parms)

    def test_info_nonexistent(self):
        _resp_xml = "<org.sonatype.nexus.rest.model.ArtifactInfoResourceResponse/>"
        _gav = "g:a:v:p"
        _ret = mock.MagicMock()
        _ret.status_code = 200
        _ret.content = _resp_xml
        self.api.web.get = mock.MagicMock(return_value=_ret)

        self.assertIsNone(self.api.info(_gav))
        _expected_parms = {"describe": "info"}
        _expected_get = posixpath.join(_nexus_url, "service", "local", "repositories", "public", "content", NexusAPI.gav_to_path(_gav))
        self.api.web.get.assert_called_once_with(_expected_get, data=None, files=None, headers=None, params=_expected_parms)

    def test_ls_nothing(self):
        self.api.web = NexusAPILsMock(_nexus_url)
        self.assertEqual(0, len(self.api.ls("surely.not.existent:artifact:9.0.9:zip")))

    def test_ls_exact(self):
        self.api.web = NexusAPILsMock(_nexus_url)
        _gav = "test.group.0.id:artifact-0:0.0.0:zip:cl"
        _ls = self.api.ls(_gav) 
        self.assertEqual(1, len(_ls))
        self.assertEqual(_ls.pop(), _gav)

    def test_ls_group(self):
        self.api.web = NexusAPILsMock(_nexus_url)
        _gav = "test.group.1.id"
        _ls = self.api.ls(_gav)
        _g_len = len(_ls)

        for _gv in _ls:
            self.assertTrue(_gv.startswith(_gav + ":"))

        _gav = ':'.join([_gav, "artifact-2"])
        _ls = self.api.ls(_gav)
        _a_len = len(_ls)
        self.assertTrue(_g_len >= _a_len)

        for _gv in _ls:
            self.assertTrue(_gv.startswith(_gav + ":"))

        _gav = ':'.join([_gav, "0.0.0"])
        _ls = self.api.ls(_gav)
        _v_len = len(_ls)
        self.assertTrue(_a_len >= _v_len)

        for _gv in _ls:
            self.assertTrue(_gv.startswith(_gav + ":"))

        _gav = ':'.join([_gav, "jar"])
        _ls = self.api.ls(_gav)
        _p_len = len(_ls)
        self.assertTrue(_v_len >= _p_len)

        for _gv in _ls:
            self.assertTrue(_gv.startswith(_gav))

        _gav = ':'.join([_gav, "cl"])
        self.assertEqual(_gav, self.api.ls(_gav).pop())

    def test_ls_filter(self):
        self.api.web = NexusAPILsMock(_nexus_url)
        _gav = 'test.group.2.id:::zip'
        _filter = 'artifact-[0-9]+:[^:]+:zip'
        _rfl = re.compile(_filter)

        _ls = self.api.ls(_gav, filter=_filter)

        for _art in _ls:
            _gg = NexusAPI.parse_gav(_art)
            self.assertEqual(_gg.get('g'), 'test.group.2.id')
            self.assertEqual(_gg.get('p'), 'zip')
            self.assertIsNotNone(_rfl.search(_art))
            
    def test_ls_filter_revert(self):
        self.api.web = NexusAPILsMock(_nexus_url)
        _gav = 'test.group.2.id::'
        _filter = 'artifact-[0-9]+:[^:]+:zip'
        _rfl = re.compile(_filter)

        _ls = self.api.ls(_gav, filter=_filter, filter_revert=True)

        for _art in _ls:
            _gg = NexusAPI.parse_gav(_art)
            self.assertEqual(_gg.get('g'), 'test.group.2.id')
            self.assertNotEqual(_gg.get('p'), 'zip')
            self.assertIsNone(_rfl.search(_art))

    def test_gav_url(self):
        self.assertEqual(self.api.gav_get_url('groupId:artifactId:version:packaging'), 
                posixpath.join(_nexus_url, "content", "repositories", "public", "groupId",
                    "artifactId", "version", "artifactId-version.packaging"))

        self.assertEqual(self.api.gav_get_url('groupId:artifactId:version:packaging:classifiler'), 
                posixpath.join(_nexus_url, "content", "repositories", "public", "groupId",
                    "artifactId", "version", "artifactId-version-classifiler.packaging"))

        self.assertEqual(self.api.gav_get_url('group.Id:artifactId:version:packaging:classifiler'), 
                posixpath.join(_nexus_url, "content", "repositories", "public", "group", "Id",
                    "artifactId", "version", "artifactId-version-classifiler.packaging"))

        self.assertEqual(self.api.gav_get_url('group.Id:artifactId:version:packaging:classifiler', repo="hellp"), 
                posixpath.join(_nexus_url, "content", "repositories", "hellp", "group", "Id",
                    "artifactId", "version", "artifactId-version-classifiler.packaging"))

        with self.assertRaises(ValueError):
            self.api.gav_get_url(None, repo="hellp")

        with self.assertRaises(ValueError):
            self.api.gav_get_url(None)
