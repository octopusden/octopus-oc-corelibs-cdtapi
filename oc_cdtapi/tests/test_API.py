import unittest
import doctest
from .. import API
from unittest.mock import ANY, MagicMock, patch, call
from http.client import HTTPMessage

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(API))
    return tests

class TestHttpAPI(unittest.TestCase):
    def setUp(self):
        self._api = API.HttpAPI(root="http://test.url", user="admin", auth='pass')
    
    @patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    def test_get_must_retry_on_failed_request(self, getconn_mock):
        getconn_mock.return_value.getresponse.side_effect = [
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=200, msg=HTTPMessage(), headers={}),
        ]

        r = self._api.get(req="tests")
        r.raise_for_status()

        assert getconn_mock.return_value.request.mock_calls == [
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
        ]
    
    @patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    def test_get_must_retry_on_failed_request_for_http(self, getconn_mock):
        _api = API.HttpAPI(root="http://test.url", user="admin", auth='pass')
        getconn_mock.return_value.getresponse.side_effect = [
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=200, msg=HTTPMessage(), headers={}),
        ]

        r = _api.get(req="tests")
        r.raise_for_status()

        assert getconn_mock.return_value.request.mock_calls == [
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
        ]
    
    @patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    def test_get_must_retry_on_failed_request_for_https(self, getconn_mock):
        _api = API.HttpAPI(root="https://test.url", user="admin", auth='pass')
        getconn_mock.return_value.getresponse.side_effect = [
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=200, msg=HTTPMessage(), headers={}),
        ]

        r = _api.get(req="tests")
        r.raise_for_status()

        assert getconn_mock.return_value.request.mock_calls == [
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
        ]

    @patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    def test_get_must_throw_on_max_retries(self, getconn_mock):
        getconn_mock.return_value.getresponse.side_effect = [
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=200, msg=HTTPMessage(), headers={}),
        ]
        with self.assertRaises(API.HttpAPIError):
            self._api.get(req="tests")

        assert getconn_mock.return_value.request.mock_calls == [
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("GET", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
        ]

    @patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    def test_post_must_retry_on_failed_request(self, getconn_mock):
        getconn_mock.return_value.getresponse.side_effect = [
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=200, msg=HTTPMessage(), headers={}),
        ]

        r = self._api.post(req="tests")
        r.raise_for_status()

        assert getconn_mock.return_value.request.mock_calls == [
            call("POST", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("POST", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("POST", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
        ]

    @patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    def test_put_must_retry_on_failed_request(self, getconn_mock):
        getconn_mock.return_value.getresponse.side_effect = [
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=200, msg=HTTPMessage(), headers={}),
        ]

        r = self._api.put(req="tests")
        r.raise_for_status()

        assert getconn_mock.return_value.request.mock_calls == [
            call("PUT", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("PUT", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("PUT", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
        ]

    @patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    def test_delete_must_retry_on_failed_request(self, getconn_mock):
        getconn_mock.return_value.getresponse.side_effect = [
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=200, msg=HTTPMessage(), headers={}),
        ]

        r = self._api.delete(req="tests")
        r.raise_for_status()

        assert getconn_mock.return_value.request.mock_calls == [
            call("DELETE", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("DELETE", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("DELETE", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
        ]

    @patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    def test_head_must_retry_on_failed_request(self, getconn_mock):
        getconn_mock.return_value.getresponse.side_effect = [
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=401, msg=HTTPMessage(), headers={}),
            MagicMock(status=200, msg=HTTPMessage(), headers={}),
        ]

        r = self._api.head(req="tests")
        r.raise_for_status()

        assert getconn_mock.return_value.request.mock_calls == [
            call("HEAD", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("HEAD", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
            call("HEAD", "/tests", body=None, headers=ANY, chunked=False, preload_content=False, decode_content=False, enforce_content_length=True),
        ]
