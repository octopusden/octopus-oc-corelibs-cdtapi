#!/usr/bin/env python3

import unittest
import unittest.mock
from ..RundeckAPI import RundeckAPI
import posixpath
from ..API import HttpAPIError
import json
from tempfile import TemporaryFile
import os
import requests.status_codes

class TestRundeckApi(unittest.TestCase):
    def setUp(self):
        self._url = "https://rundeck.example.com"
        self._api_version = 17
        self._rundeck = RundeckAPI(url=self._url, user="test_user", password="test_password")
        self._rundeck.web.get = unittest.mock.MagicMock()
        self._rundeck.web.post = unittest.mock.MagicMock()
        self._rundeck.web.put = unittest.mock.MagicMock()
        self._rundeck.web.delete = unittest.mock.MagicMock()
        self._rundeck._api_version = self._api_version
        self.__headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        self.__cookies = {"JSESSIONID": "test_session_cookie"}
        self._rundeck._auth_cookie = self.__cookies

    def test_init(self):
        self.assertEqual(self._rundeck.root, "https://rundeck.example.com")

    def test_api_version__get(self):
        self._rundeck._api_version = None
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
        _rtv = unittest.mock.MagicMock()
        _rv = {"test": "keys"}
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        _rtv.status_code = requests.codes.ok
        self._rundeck.web.get.return_value=_rtv
        self.assertEqual(self._rundeck.key_storage__list(), _rv)
        self._rundeck.web.get.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "storage", "keys"),
                headers = self.__headers, cookies = self.__cookies, params=None, data=None, files=None)

    def test_key_storage_list__with_path(self):
        _rtv = unittest.mock.MagicMock()
        _rv = {"test": "keys"}
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        _rtv.status_code = requests.codes.ok
        self._rundeck.web.get.return_value=_rtv
        self.assertEqual(self._rundeck.key_storage__list("simplepath"), _rv)
        self._rundeck.web.get.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "storage", "keys", "simplepath"),
                headers = self.__headers, cookies = self.__cookies, params=None, data=None, files=None)

    def test_key_storage_exists__true(self):
        _rtv = unittest.mock.MagicMock()
        _rv = {"test": "keys"}
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        _rtv.status_code = requests.codes.ok
        self._rundeck.web.get.return_value=_rtv
        self.assertTrue(self._rundeck.key_storage__exists("simplepath"))
        self._rundeck.web.get.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "storage", "keys", "simplepath"),
                headers = self.__headers, cookies = self.__cookies, params=None, data=None, files=None)

    def test_key_storage_exists__false(self):
        _rtv = unittest.mock.MagicMock()
        _rv = {}
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        _rtv.status_code = requests.codes.not_found
        self._rundeck.web.get.return_value=_rtv
        self.assertFalse(self._rundeck.key_storage__exists("simplepath"))
        self._rundeck.web.get.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "storage", "keys", "simplepath"),
                headers = self.__headers, cookies = self.__cookies, params=None, data=None, files=None)

    def test_key_storage_upload__wrong_arg(self):
        with self.assertRaises(ValueError):
            self._rundeck.key_storage__upload(None, "badkey", "content")

        with self.assertRaises(ValueError):
            self._rundeck.key_storage__upload("testProject", None, "content")

        with self.assertRaises(ValueError):
            self._rundeck.key_storage__upload("testProject", "testKey", None)

    def test_key_storage_upload__existing(self):
        self._rundeck.key_storage__exists = unittest.mock.MagicMock(return_value=True)
        _rtv = unittest.mock.MagicMock()
        _rv = {"test": "keys"}
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        _rtv.status_code = requests.codes.ok
        self._rundeck.web.put.return_value=_rtv
        self.assertEqual(_rv, self._rundeck.key_storage__upload("testKey", "private", "testdata"))
        self._rundeck.web.put.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "storage", "keys", "testKey"),
                cookies=self.__cookies,
                headers={"Content-type": "application/octet-stream", "Accept": "application/json"},
                data="testdata", params=None, files=None)
        self._rundeck.web.post.assert_not_called()

    def test_key_storage_upload__new(self):
        self._rundeck.key_storage__exists = unittest.mock.MagicMock(return_value=False)
        _rtv = unittest.mock.MagicMock()
        _rv = {"test": "keys"}
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        _rtv.status_code = requests.codes.ok
        self._rundeck.web.post.return_value=_rtv
        self.assertEqual(_rv, self._rundeck.key_storage__upload("testKey", "password", "testdata"))
        self._rundeck.web.post.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "storage", "keys", "testKey"),
                cookies=self.__cookies,
                headers={"Content-type": "application/x-rundeck-data-password", "Accept": "application/json"},
                data="testdata", params=None, files=None)
        self._rundeck.web.put.assert_not_called()

    def test_key_storage__delete_existing(self):
        self._rundeck.key_storage__exists = unittest.mock.MagicMock(return_value=True)
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.no_content
        self._rundeck.web.delete.return_value=_rtv
        self.assertEqual(requests.codes.no_content, self._rundeck.key_storage__delete("testKey"))
        self._rundeck.web.delete.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "storage", "keys", "testKey"),
                cookies=self.__cookies, headers=self.__headers, data=None, params=None, files=None)

    def test_key_storage__delete_missing(self):
        self._rundeck.key_storage__exists = unittest.mock.MagicMock(return_value=False)
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.no_content
        self._rundeck.web.delete.return_value=_rtv
        self.assertEqual(requests.codes.not_found, self._rundeck.key_storage__delete("testKey"))
        self._rundeck.web.delete.assert_not_called()

    def test_project__list(self):
        _rv = ["testProjectList"]
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.get.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.project__list())
        self._rundeck.web.get.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "projects"),
                headers=self.__headers, cookies=self.__cookies, data=None, params=None, files=None)

    def test_project__info_ok(self):
        _project = "TestProject"
        _rv = {"testProjectInfo": _project}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.get.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.project__info(_project))
        self._rundeck.web.get.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "project", _project),
                headers=self.__headers, cookies=self.__cookies, data=None, params=None, files=None)

    def test_project__info__wrong_arg(self):
        _project = "TestProject"
        _rv = {"testProjectInfo": _project}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.get.return_value = _rtv

        with self.assertRaises(ValueError):
            self._rundeck.project__info("")

        self._rundeck.web.get.assert_not_called()

    def test_project__exists__true(self):
        _project = "TestProject"
        _rv = {"testProjectInfo": _project}
        _rtv = unittest.mock.MagicMock()
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        _rtv.status_code = requests.codes.ok
        self._rundeck.web.get.return_value=_rtv
        self.assertTrue(self._rundeck.project__exists(_project))
        self._rundeck.web.get.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "project", _project),
                headers = self.__headers, cookies = self.__cookies, params=None, data=None, files=None)

    def test_project__exists__false(self):
        _project = "TestProject"
        _rtv = unittest.mock.MagicMock()
        _rv = {}
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        _rtv.status_code = requests.codes.not_found
        self._rundeck.web.get.return_value=_rtv
        self.assertFalse(self._rundeck.project__exists(_project))
        self._rundeck.web.get.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "project", _project),
                headers = self.__headers, cookies = self.__cookies, params=None, data=None, files=None)

    def test_project__config_ok(self):
        _project = "TestProject"
        _rv = {"testProjectName": _project, "configuration": "testConfiguration"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.get.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.project__get_configuration(_project))
        self._rundeck.web.get.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "project", _project, "config"),
                headers=self.__headers, cookies=self.__cookies, data=None, params=None, files=None)

    def test_project__config__wrong_arg(self):
        _project = "TestProject"
        _rv = {"testProjectName": _project, "configuration": "testConfiguration"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.get.return_value = _rtv

        with self.assertRaises(ValueError):
            self._rundeck.project__get_configuration("")

        self._rundeck.web.get.assert_not_called()

    def test_project__update__new_properties(self):
        self._rundeck.project__exists = unittest.mock.MagicMock(return_value=False)
        _project = "testProject"
        _project_definition = f"project.name={_project}"
        _expected_data = {"name": _project, "config": {"project.name": _project}}
        _rv = {"testProjectName": _project, "configuration": "testConfiguration"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.post.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.project__update(_project_definition))
        self._rundeck.web.post.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "projects"),
                headers=self.__headers, cookies=self.__cookies, data=json.dumps(_expected_data), params=None, files=None)
        self._rundeck.web.put.assert_not_called()
        
    def test_project__update__new_short_json(self):
        self._rundeck.project__exists = unittest.mock.MagicMock(return_value=False)
        _project = "testProject"
        _project_definition = '{"project.name": "%s"}' % _project
        _expected_data = {"name": _project, "config": {"project.name": _project}}
        _rv = {"testProjectName": _project, "configuration": "testConfiguration"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.post.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.project__update(_project_definition))
        self._rundeck.web.post.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "projects"),
                headers=self.__headers, cookies=self.__cookies, data=json.dumps(_expected_data), params=None, files=None)
        self._rundeck.web.put.assert_not_called()

    def test_project__update__new_full_json(self):
        self._rundeck.project__exists = unittest.mock.MagicMock(return_value=False)
        _project = "testProject"
        _project_definition = '{"name": "%s", "config":{"project.someproperty": "somevalue"}}' % _project
        _expected_data = {"name": _project, "config": {"project.someproperty": "somevalue"}}
        _rv = {"testProjectName": _project, "configuration": "testConfiguration"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.post.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.project__update(_project_definition))
        self._rundeck.web.post.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "projects"),
                headers=self.__headers, cookies=self.__cookies, data=json.dumps(_expected_data), params=None, files=None)
        self._rundeck.web.put.assert_not_called()

    def test_project__update__existing_properties(self):
        self._rundeck.project__exists = unittest.mock.MagicMock(return_value=True)
        _project = "testProject"
        _project_definition = f"project.name={_project}"
        _expected_data = {"project.name": _project}
        _rv = {"testProjectName": _project, "configuration": "testConfiguration"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.put.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.project__update(_project_definition))
        self._rundeck.web.put.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "project", _project, "config"),
                headers=self.__headers, cookies=self.__cookies, data=json.dumps(_expected_data), params=None, files=None)
        self._rundeck.web.post.assert_not_called()
        
    def test_project__update__existing_short_json(self):
        self._rundeck.project__exists = unittest.mock.MagicMock(return_value=True)
        _project = "testProject"
        _project_definition = '{"project.name": "%s"}' % _project
        _expected_data = {"project.name": _project}
        _rv = {"testProjectName": _project, "configuration": "testConfiguration"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.put.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.project__update(_project_definition))
        self._rundeck.web.put.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "project", _project, "config"),
                headers=self.__headers, cookies=self.__cookies, data=json.dumps(_expected_data), params=None, files=None)
        self._rundeck.web.post.assert_not_called()

    def test_project__update__existing_full_json(self):
        self._rundeck.project__exists = unittest.mock.MagicMock(return_value=True)
        _project = "testProject"
        _project_definition = '{"name": "%s", "config":{"project.someproperty": "somevalue"}}' % _project
        _expected_data = {"project.someproperty": "somevalue"}
        _rv = {"testProjectName": _project, "configuration": "testConfiguration"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.put.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.project__update(_project_definition))
        self._rundeck.web.put.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "project", _project, "config"),
                headers=self.__headers, cookies=self.__cookies, data=json.dumps(_expected_data), params=None, files=None)
        self._rundeck.web.post.assert_not_called()

    def test_project__update__wrong_arg(self):
        # no name specified at all
        _project_definition = {"project.someproperty": "somevalue"}

        with self.assertRaises(ValueError):
            self._rundeck.project__update(_project_definition)

        # config present but without name
        _project_definition = {"config":{"project.someproperty": "somevalue"}}

        with self.assertRaises(ValueError):
            self._rundeck.project__update(_project_definition)

        # name present but no config
        _project_definition = {"name": "someName"}

        with self.assertRaises(ValueError):
            self._rundeck.project__update(_project_definition)


    def test_project__delete_existing(self):
        self._rundeck.project__exists = unittest.mock.MagicMock(return_value=True)
        _project = "testProject"
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.no_content;
        self._rundeck.web.delete.return_value = _rtv
        self.assertEqual(requests.codes.no_content, self._rundeck.project__delete(_project))
        self._rundeck.web.delete.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), "project", _project),
                headers=self.__headers, cookies=self.__cookies, data=None, params=None, files=None)

    def test_project__delete_missing(self):
        self._rundeck.project__exists = unittest.mock.MagicMock(return_value=False)
        _project = "testProject"
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.no_content;
        self._rundeck.web.delete.return_value = _rtv
        self.assertEqual(requests.codes.not_found, self._rundeck.project__delete(_project))
        self._rundeck.web.delete.assert_not_called()

    def test_scm_setup__ok_short_json(self):
        _project = "TestProject"
        _integration = "import"
        _plugin_type = "test-scm-plugin-type"
        _scm_def = {"property": "value"}
        _expected_data = {"config": {"property": "value"}}
        _rv = {"scm": "testScm"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.post.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.scm__setup(_project, _integration, _plugin_type, _scm_def))
        self._rundeck.web.post.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), 
                    "project", _project, "scm", _integration, "plugin", _plugin_type, "setup"),
                data=json.dumps(_expected_data),
                headers=self.__headers, cookies=self.__cookies, params=None, files=None)

    def test_scm_setup__ok_full_json(self):
        _project = "TestProject"
        _integration = "import"
        _plugin_type = "test-scm-plugin-type"
        _scm_def = {"config": {"property": "value"}}
        _expected_data = _scm_def
        _rv = {"scm": "testScm"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.post.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.scm__setup(_project, _integration, _plugin_type, _scm_def))
        self._rundeck.web.post.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), 
                    "project", _project, "scm", _integration, "plugin", _plugin_type, "setup"),
                data=json.dumps(_expected_data),
                headers=self.__headers, cookies=self.__cookies, params=None, files=None)

    def test_scm_setup__wrong_args(self):
        with self.assertRaises(ValueError):
            self._rundeck.scm__setup("", "import", "test-scm-plugin-type", {"test": "def"})

        with self.assertRaises(ValueError):
            self._rundeck.scm__setup("project", "", "test-scm-plugin-type", {"test": "def"})

        with self.assertRaises(ValueError):
            self._rundeck.scm__setup("project", "wrong", "test-scm-plugin-type", {"test": "def"})

        with self.assertRaises(ValueError):
            self._rundeck.scm__setup("project", "import", "", {"test": "def"})

        with self.assertRaises(ValueError):
            self._rundeck.scm__setup("project", "export", "test-scm-plugin-type", {})

        with self.assertRaises(ValueError):
            self._rundeck.scm__setup("project", "import", "test-scm-plugin-type", None)

        with self.assertRaises(ValueError):
            self._rundeck.scm__setup(None, "export", "test-scm-plugin-type", {"test": "def"})

    def test_scm_enable__true(self):
        _project = "TestProject"
        _integration = "import"
        _plugin_type = "test-scm-plugin-type"
        _rv = {"scm": "testScm"}
        _rtv = unittest.mock.MagicMock()
        _rtv.status_code = requests.codes.ok
        _rtv.json = unittest.mock.MagicMock(return_value=_rv)
        self._rundeck.web.post.return_value = _rtv
        self.assertEqual(_rv, self._rundeck.scm__enable(_project, _integration, _plugin_type, _scm_def, True))
        self._rundeck.web.post.assert_called_once_with(
                posixpath.join(self._url, "api", str(self._api_version), 
                    "project", _project, "scm", _integration, "plugin", _plugin_type, "enable"),
                data=None,
                headers=self.__headers, cookies=self.__cookies, params=None, files=None)

    def test_scm_enable__false(self):
        pass

    def test_scm_enable__wrong_args(self):
        pass

    def test_scm_get_action_inputs__ok(self):
        pass

    def test_scm_get_action_inputs__wrong_args(self):
        pass

    def test_scm__perform_ok(self):
        pass

    def test_scm__perform_wrong_args(self):
        pass

    def test_scm_perform_all_actions__import_ok(self):
        pass

    def test_scm_perform_all_actions__export_ok(self):
        pass
    def test_scm_perform_all_actions__wrong_args(self):
        pass

    def test_scm_status__ok(self):
        pass

    def test_scm_status__wrong_args(self):
        pass
