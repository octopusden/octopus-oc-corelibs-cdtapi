#!/usr/bin/env python3

import unittest
import unittest.mock
from ..RundeckAPI import RundeckAPI
import posixpath
from ..API import HttpAPIError
import json
from tempfile import TemporaryFile
import os

class TestRundeckApi(unittest.TestCase):
    def setUp(self):
        self._url = "https://rundeck.example.com"
        self._rundeck = RundeckAPI(url=self._url, user="test_user", password="test_password")
        self._rundeck.get = unittest.mock.MagicMock()
        self._rundeck.post = unittest.mock.MagicMock()
        self._rundeck.put = unittest.mock.MagicMock()
        self._rundeck.delete = unittest.mock.MagicMock()
        self._rundeck._auth_cookie = {"JSESSIONID": "test_session_cookie"}
        self._rundeck._api_version = 17

    @property
    def __headers(self):
        return {'Content-type': 'application/json', 'Accept': 'application/json'}

    def test_init(self):
        self.assertEqual(self._rundeck.root, "https://rundeck.example.com")

    def test_api_version__get(self):
        self.assertIsNone(self._rundeck._api_version)
        _rvd = {"apiversion": 36}
        _rv = unittest.mock.MagicMock()
        _rv.json = unittest.mock.MagicMock(return_value=_rvd)
        self._rundeck.web.get = unittest.mock.MagicMock(return_value = _rv)
        self.assertEqual(self._rundeck.api_version, 36)
        self._rundeck.web.get.assert_called_once_with(
                posixpath.join(self._url, "api", "unsupported"),
                headers=self.__headers)

    def test_api_version__ready(self):
        self.assertEqual(self._rundeck.api_version, 17)

    def test_cookies__ready(self):
        self.assertEqual(self._rundeck.cookies, {"JSESSIONID": "test_session_cookie"})

    def test_cookies__token(self):
        self._rundeck._auth_cookie = None
        self._rundeck._token = "test_token"
        self.assertIsNone(self._rundeck.cookies)

    def test_cookies__get_success(self):
        self._rundeck._auth_cookie = None
        _rv = unittest.mock.MagicMock()
        _rv.cookies = {"JSESSIONID": "another_test_session_cookie"}
        _rc = unittest.mock.MagicMock()
        _rc.url = posixpath.join(self._url, "user", "login")
        _rc.history = [_rv]
        self._rundeck.web.post = unittest.mock.MagicMock(return_value=_rc)
        self.assertEqual(self._rundeck.cookies, {"JSESSIONID": "another_test_session_cookie"})
        self._rundeck.web.post.assert_called_once_with(
                posixpath.join(self._url, "j_security_check"),
                data={"j_username": "test_user", "j_password": "test_password"},
                allow_redirects=True)

    def test_cookies__get_failed(self):
        self._rundeck._auth_cookie = None
        _rv = unittest.mock.MagicMock()
        _rv.cookies = {"JSESSIONID": "another_test_session_cookie"}
        _rc = unittest.mock.MagicMock()
        _rc.url = posixpath.join(self._url, "user", "error")
        _rc.history = [_rv]
        self._rundeck.web.post = unittest.mock.MagicMock(return_value=_rc)
        with self.assertRaises(HttpAPIError):
            self._rundeck.cookies

        self._rundeck.web.post.assert_called_once_with(
                posixpath.join(self._url, "j_security_check"),
                data={"j_username": "test_user", "j_password": "test_password"},
                allow_redirects=True)


    def test_to_dict__dict(self):
        __dict = {"test": "test"}
        self.assertEqual(self._rundeck._to_dict(__dict), __dict)

    def test_to_dict__str_json(self):
        __dict = {"test": "test"}
        self.assertEqual(self._rundeck._to_dict(json.dumps(__dict)), __dict)

    def test_to_dict__str_property(self):
        __dict = {"test": "test"}
        self.assertEqual(self._rundeck._to_dict("test = test"), __dict)

    def test_to_dict__file_json(self):
        __dict = {"test": "test"}
        _x = TemporaryFile(mode='rt+')
        _x.write(json.dumps(__dict))
        _x.seek(0, os.SEEK_SET)
        self.assertEqual(self._rundeck._to_dict(_x), __dict)
        _x.close()

    def test_to_dict__file_property(self):
        __dict = {"test": "test"}
        _x = TemporaryFile(mode='rt+')
        _x.write("test = test")
        _x.seek(0, os.SEEK_SET)
        self.assertEqual(self._rundeck._to_dict(_x), __dict)
        _x.close()

    def test_key_storage_list__no_path(self):
        _rtv = unittest.mock.MagicMock
        _rv = {"test": "keys"}
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.get.return_value=_rtv
        self.assertEqual(self._rundeck.key_storage__list(), _rv)
        self._rundeck.get.assert_called_once_with(
                posixpath.join(self._url, "api", 
