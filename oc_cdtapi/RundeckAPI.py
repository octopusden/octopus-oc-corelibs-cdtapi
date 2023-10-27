#!/usr/bin/env python3

# implementation of Rundeck REST API calls

import sys
import json

if sys.version_info.major < 3:
    raise NotImplementedError("Please use Python version 3 or later")

import logging
from .API import HttpAPI, HttpAPIError
import posixpath #since urljoin does not control backslashes

# disable insecure requests warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests.status_codes

class RundeckAPI(HttpAPI):
    def __init__(self, url, user=None, password=None, token=None):
        """
        Basic initialization.
        Authorization may be with user/password pair or token
        :param str url: Rundeck URL
        :param str user: Rundeck user
        :param str password: Rundeck password
        :param str token: Rundeck token
        """

        self._logger = logging.getLogger(__name__)
        self._token = token
        self._env_prefix = "RUNDECK"
        self._api_version = None
        # base class stores these two into web session auth, but it is useless for Rundeck
        self._user = user
        self._password = password

        super().__init__(root=url, user=user, auth=password)
        self._auth_cookie = None

    def __to_dict(self, object_d):
        """
        Convert to dictionary
        :param _io.TextIOWrapper object_d: file-like object opened in string mode, considered as '.json' or '.properties' file
        :param str object_d: a string with JSON or .properties definition
        :param dict object_d: a ditionary object
        :return dict:
        """
        self._logger.info(f"Trying to convert [{type(object_d)}] to [dict]...")

        if isinstance(object_d, dict):
            self._logger.debug("Dictionary providied, returning 'as is'")
            return object_d

        if hasattr(object_d, "read"):
            self._logger.debug("File-like object provided, reading content")
            object_d = object_d.read()

        # try to parse JSON and return it if OK
        # NOTE: if 'object_d' has wrong type then TypeError will be raised and NOT handled below
        try:
            return json.loads(object_d)
        except json.decoder.JSONDecodeError:
            self._logger.info("Unable to decode definition as [JSON] object, parsing as .properties")
            pass

        _result = dict()
        for _line in list(map(lambda x: x.strip(), object_d.splitlines())):
            if not _line:
                # empty line
                continue

            if _line.startswith('#'):
                # comment found
                continue

            if '=' not in _line:
                raise SyntaxError(f"Invalid property line: [{_line}]")

            _key,_value = _line.split("=", 1)
            _result[_key.strip()] = _value.strip()

        return _result

    @property
    def api_version(self):
        """
        Return current API version
        :return int:
        """
        if not self._api_version:
            self._get_api_version()

        return self._api_version

    @property
    def headers(self):
        """
        Return default headers basing on authorization method
        :return dict:
        """
        _result = {
                "Content-type": "application/json",
                "Accept": "application/json"
                }

        if self._token:
            _result["X-Rundeck-Auth-Token"] = self._token

        return _result

    def _get_api_version(self):
        """
        Obtain API version from Rundeck error response
        """
        self._logger.info("Try to detect Rundeck API version...")
        # Here we are forced to skip raising exception since we know this MUST be an error
        _tmp_exceptions = (self.raise_exception_low, self.raise_exception_high)
        self.raise_exception_low = 0
        self.raise_exception_high = 999
        _response = self.web.get(super().re(["api", "unsupported"]), headers={
            'Content-type': 'application/json', "Accept": 'application/json'})
        self._logger.debug(f"Response for API: {_response.json()}")
        # restore exceptions raising
        self.raise_exception_low, self.raise_exception_high = _tmp_exceptions
        self._api_version = _response.json().get("apiversion")
        self._logger.info(f"Rundeck API version: [{self._api_version}]")

    @property
    def cookies(self):
        """
        Return authorization cookie
        :return dict:
        """

        if self._token:
            self._logger.debug("Token provided, skipping cookie obtaining")
            return None

        if not self._auth_cookie:
            self._get_auth_cookie()

        return self._auth_cookie

    def _get_auth_cookie(self):
        """
        Obtain authorization cookie
        """
        self._logger.info("Try to obtain auth cookie...")
        _rq_params = {"j_username": self._user, "j_password": self._password}
        _response = self.web.post(super().re(["j_security_check"]), data=_rq_params, allow_redirects=True)
        self._logger.debug(f"Authorization response: {_response.status_code}")

        #we should filter all redirects in the history and check where we are redirected to
        _response.raise_for_status()

        # the auth was successful if all redirects in the chain does not lead to $RUNDECK_SERVER_URL/user/error
        # see https://docs.rundeck.com/docs/api/rundeck-api.html#password-authentication for details
        self._logger.debug(f"Response final url: {_response.url}")
        _auth_success = not _response.url.endswith(posixpath.join("user", "error"))
        self._logger.info(f"Authorization result: {_auth_success}")

        if not _auth_success:
            raise HttpAPIError(
                    code=requests.codes.unauthorized,
                    url=_response.url,
                    resp=_response,
                    text="User-Password authentication failed")

        # the lates cookie is the actual one, we should get it
        _t = list(_response.history).pop(0).cookies
        self._auth_cookie = dict((_x, _t.get(_x)) for _x in ["JSESSIONID"])
        self._logger.info("Auth cookie obtained")

    def __append_path_list(self, req, apnd):
        """
        Append request URL with appendix given to get rid of TypeError
        :param str req: a source request
        :param str apnd: appendix
        :return list:
        """

        if not isinstance(req, list):
            req = list(filter(lambda x: x, posixpath.split(req)))

        if not isinstance(apnd, list):
            apnd = list(filter(lambda x: x, posixpath.split(apnd)))

        return req + apnd

    def re(self, req):
        """
        Preprocess request URL
        """
        if not isinstance(req, list): 
            req = list(filter(lambda x: x, posixpath.split(req)))

        req = self.__append_path_list(["api", str(self.api_version)], req)
        return super().re(req)

    def key_storage__list(self, path=None):
        """
        list internal KeyStorage content
        also provides metadata if 'path' specifies a key
        :param str path: internal path to list
        :return dict: a dictionary with list of "resources" with all keys metadata if "path" not given
        :return dict: a dictionary with direct key metadata if single key given as "path"
        """
        self._logger.info(f"Listing keys, path: [{path}]")
        _req = ["storage", "keys"]

        if path:
            _req =self.__append_path_list(_req, path)

        return self.get(_req, headers=self.headers, cookies=self.cookies).json()

    def __object_exists(self, method, object_id):
        try:
            method(object_id)
        except HttpAPIError as _e:
            if _e.code == requests.codes.not_found:
                return False

            raise

        return True

    def key_storage__exists(self, path):
        """
        Check if key exists
        :param str path: internal Rundeck path to the key to check
        :return bool:
        """
        self._logger.info(f"Check key exists: [{path}]")
        return self.__object_exists(self.key_storage__list, path)

    def key_storage__upload(self, path, key_type, content):
        """
        Create or update a key
        :param str path: internal KeyStorage path
        :param str key_type: type of key. May be set as 'application/xxx' directly or via aliases supported:
                             private, public, password
        :param bytes content: bytes array provides a password
        :return dict:
        """
        self._logger.info(f"Try to upload key [{path}], type [{key_type}]")
        if not path:
            raise ValueError("Key path is mandatory")

        if not key_type:
            raise ValueError("Key type is mandatory")

        if not content:
            raise ValueError("Key content is mandatory")

        # if key exists then we should update its conkey_storage__listtent using PUT method
        # otherwise we have to create new one using POST method
        _req = self.__append_path_list(["storage", "keys"], path)
        _headers = self.headers

        # key type should be one of: 
        ###     application/octet-stream specifies a private key
        ### application/pgp-keys specifies a public key
        ### application/x-rundeck-data-password specifies a password
        __keytype_map = {
                "private": "application/octet-stream",
                "public": "application/pgp-keys",
                "password": "application/x-rundeck-data-password" }

        # use a value from a map if given, or provide 'as is' if not
        key_type = __keytype_map.get(key_type, key_type)
        self._logger.debug(f"Key type after adjustment: [{key_type}]")
        _headers["Content-type"] = __keytype_map.get(key_type, key_type)
        _method = self.put if self.key_storage__exists(path) else self.post
        return _method(req=_req, headers=_headers, data=content).json()

    def key_storage__delete(self, path):
        """
        Delete a key if exists
        :param str path: path to a key to remove
        :return dict:
        """
        self._loger.info(f"Deleting key: [{path}]")
        if not self.key_storage__exists(path):
            self._logger.debug(f"{path} does not exist")
            return

        _req = self.__append_path_list(["storage", "keys"], path)
        return self.delete(_req).json()

    def project__list(self):
        """
        Get short metadata for all projects
        :param str project: project name; list all projects if not specified
        :return list: list of dictionaries with all projects short metadata
        """
        self._logger.info("Lsting projects")
        _req = ["projects"]
        return self.get(_req, headers=self.headers, cookies=self.cookies).json()

    def project__info(self, project):
        """
        Get full project metadata
        :param str project: project name
        :return dict: dictionary with single project information if one specified
        """
        self._logger.info(f"Get project info: [{project}]")

        if not project:
            raise ValueEror("Project is mandatory")

        _req = ["project", project]
        return self.get(_req, headers=self.headers, cookies=self.cookies).json()

    def project__exists(self, project):
        """
        check if project with a name given exists
        :param str project: project name
        :return bool:
        """
        self._logger.info(f"Check project exists: [{project}]")
        return self.__object_exists(self.project__info, project)

    def project__get_configuration(self, project):
        """
        Get project configuration parameters
        :param str project: project name
        :return dict:
        """
        self._logger.info(f"Getting project configuration: [{project}]")
        _req = ["project", project, "config"]
        return self.get(_req, headers=self.headers, cookies=self.cookies).json()

    def project__update(self, definition):
        """
        Create or update project
        :param BufferIO definition: file-like object for project definition
        :param str definition: project definition as read of 'project.properties' file
        :param dict definition: project definition dictionary {"propname":"propvalue", ...}
        :param _io.TextIOWrapper definition: project definition file-like object
        :return dict:
        """
        self._logger.info(f"Upating project configuration: type of definition: [{type(definition)}]")

        if not definition:
            raise ValueError("Project definition is mandatory")

        definition = self.__to_dict(definition)
        project = definition.get("project.name") or \
                definition.get("name") or \
                definition.get("config", dict()).get("project.name")

        self._logger.info(f"Project name: [{project}]")

        if not project:
            raise ValueError("Project name is not specified in the definition")

        # prepare project name and configuration
        if not all(list(map(lambda _x: definition.get(_x), ["name", "config"]))):
            self._logger.debug(f"Both 'configuration' and 'name' absent in the definition, appending all")
            definition={"name": project, "config": definition}
        elif definition.get("config"):
            self._logger.debug(f"Project [{project}] configuration present but 'name' absent in the dict")
            definition["name"] = project
        elif definition.get("name"):
            raise ValueError(f"Project definition has wrong format: 'config' should be specified if 'name' key given")

        self._logger.log(5, f"Project definition: {str(definition)}")

        # if project exists - perform an update
        # create new one otherwise

        if self.project__exists(project):
            self._logger.info(f"Project [{project}] exists, performing an update...")
            return self.put(
                ["project", project, "config"],
                data=json.dumps(definition.get("config")),
                headers=self.headers,
                cookies=self.cookies).json()

        self._logger.info(f"Project [{project}] does not exist, creating new one")
        return self.post("projects", data=json.dumps(definition), headers=self.headers, cookies=self.cookies).json()

    def project__delete(self, project):
        """
        Delete a project
        :param str project: project name
        :return int: status code
        """
        self._logger.info(f"Deleting project [{project}]")

        if not project:
            raise ValueError("Project name is mandatory")

        return self.delete(["project", project], headers=self.headers, cookies=self.cookies).status_code

    def scm__setup(self, project, integration, plugin_type, definition):
        """
        Setup SCM for a project
        :param str project: project name
        :param str integration: one of: "import", "export"
        :param str plugin_type: plugin to configure
        :param str definition: string with SCM parameters
        :param dict definition: dictionary with SCM parameters
        :param _io.TextIOWrapper definition: file-like object with SCM parameters opened in string mode
        :return dict:
        """
        self._logger.info(" ".join([
            "Upating project SCM configuration:",
            f"project: [{project}], integration: [{integration}], plugin_type: [{plugin_type}]",
            f"type of definition: [{type(definition)}]"]))

        # checking arguments
        if not definition:
            raise ValueError("SCM definition is mandatory")

        if not project:
            raise ValueError("Project name is mandatory")

        if integration not in ["import", "export"]:
            raise ValueError(f"Unsupported SCM integration type: [{integration}]")

        if not plugin_type:
            raise ValueError("Plugin type is mandatory")
        
        definition = self.__to_dict(definition)

        # configuration may be outside of a dict
        if not definition.get("config"):
            definition = {"config": definition}

        self._logger.log(5, f"Final definition is: [{definition}]")

        _req = ["project", project, "scm", integration, "plugin", plugin_type, "setup"]

        return self.post(_req, headers=self.headers, cookies=self.cookies, data=json.dumps(definition)).json()

    def scm__enable(self, project, integration, plugin_type, enable=False):
        """
        Turn on/off SCM for a project
        :param str project: project name
        :param str integration: one of: "import", "export"
        :param str plugin_type: plugin to configure
        :param bool enable: disable if set to False, enable otherwise
        :return dict:
        """
        self._logger.info(
                " ".join([
                    'Enable' if enable else 'Disable',
                    f"SCM for project [{project}], integration [{integration}], plugin_type [{plugin_type}]"]))

        # checking arguments
        if not project:
            raise ValueError("Project name is mandatory")

        if integration not in ["import", "export"]:
            raise ValueError(f"Unsupported SCM integration type: [{integration}]")

        if not plugin_type:
            raise ValueError("Plugin type is mandatory")
        
        _req = ["project", project, "scm", integration, "plugin", plugin_type, "enable" if enable else "disable"]

        return self.post(_req, headers=self.headers, cookies=self.cookies).json()

    def scm__perform(self):
        pass

    def scm__status(self, project, integration):
        """
        Get SCM plugin status for a project
        :param str project: project name
        :param str integration: one of: "import", "export"
        :return dict:
        """
        self._logger.info(
                f"Get SCM status for project [{project}], integration [{integration}]")

        # checking arguments
        if not project:
            raise ValueError("Project name is mandatory")

        if integration not in ["import", "export"]:
            raise ValueError(f"Unsupported SCM integration type: [{integration}]")

        _req = ["project", project, "scm", integration, "status"]

        return self.get(_req, headers=self.headers, cookies=self.cookies).json()
