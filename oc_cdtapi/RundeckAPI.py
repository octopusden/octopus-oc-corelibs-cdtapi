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
        self.__args_supported_values = {"scm_integration": ["import", "export"]}

        super().__init__(root=url, user=user, auth=password)
        self._auth_cookie = None

    def __check_args(self, **kwargs):
        """
        Check if integration arguments are given. Has no return value but raises ValueError if
        something goes wrong
        :param kwargs: other mandatory keyword arguments to be checked for 'positive' value
        """

        for (_k, _v) in kwargs.items():
            if not _v:
                raise ValueError(f"[{_k}] is mandatory.")
            
            _supported_values = self.__args_supported_values.get(_k)

            if not _supported_values:
                continue

            if _v not in _supported_values:
                raise ValueError(f"Unsupported value for [{_k}]: [{_v}]. Should be one of: {_supported_values}")

    def _to_dict(self, object_d):
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

        # All existing .properties parsers are too complex and not usable for our case, because of
        # Rundeck specific: all values have to be strings, regardless of their actual type.
        # That is: boolean values, for example, should be "true" or "false", not True or False
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
        self._logger.log(5, f"Response for API: {_response.json()}")
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
        self._logger.log(5, f"Authorization response: {_response.status_code}")
        _response.raise_for_status()

        #we should filter all redirects in the history and check where we are redirected to
        # the auth was successful if final redirect does not lead to $RUNDECK_SERVER_URL/user/error
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

        # the latest cookie is the actual one, we should get it
        _t = list(_response.history).pop(0).cookies
        self._auth_cookie = dict((_x, _t.get(_x)) for _x in ["JSESSIONID"])
        self._logger.info("Auth cookie obtained")

    def __append_path_list(self, req, apnd):
        """
        Append request URL with appendix given to get rid of TypeError
        :param str req: a source request
        :param str apnd: appendix
        :return list:https://github.com/octopusden/octopus-di-rundeck/pull/4
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

    def key_storage__list(self, key_path=None):
        """
        list internal KeyStorage content
        also provides metadata if 'key_path' specifies a key
        :param str key_path: internal key_path to list
        :return dict: a dictionary with list of "resources" with all keys metadata if "key_path" not given
        :return dict: a dictionary with direct key metadata if single key given as "key_path"
        """
        self._logger.info(f"Listing keys, key_path: [{key_path}]")
        _req = ["storage", "keys"]

        if key_path:
            _req = self.__append_path_list(_req, key_path)

        return self.get(_req, headers=self.headers, cookies=self.cookies).json()

    def __object_exists(self, method, object_id):
        try:
            method(object_id)
        except HttpAPIError as _e:
            if _e.code == requests.codes.not_found:
                return False

            raise

        return True

    def key_storage__exists(self, key_path):
        """
        Check if key exists
        :param str key_path: internal Rundeck key_path to the key to check
        :return bool:
        """
        self._logger.info(f"Check key exists: [{key_path}]")
        return self.__object_exists(self.key_storage__list, key_path)

    def key_storage__upload(self, key_path, key_type, key_data):
        """
        Create or update a key
        :param str key_path: internal KeyStorage key_path
        :param str key_type: type of key. May be set as 'application/xxx' directly or via aliases supported:
                             private, public, password
        :param bytes key_data: bytes array provides a password
        :return dict:
        """
        self._logger.info(f"Try to upload key [{key_path}], type [{key_type}]")
        self.__check_args(key_path=key_path, key_type=key_type, key_data=key_data)

        # if key exists then we should update its conkey_storage__listtent using PUT method
        # otherwise we have to create new one using POST method
        _req = self.__append_path_list(["storage", "keys"], key_path)
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
        _headers["Content-type"] = key_type
        _method = self.put if self.key_storage__exists(key_path) else self.post
        return _method(req=_req, headers=_headers, cookies=self.cookies, data=key_data).json()

    def key_storage__delete(self, key_path):
        """
        Delete a key if exists
        :param str key_path: key_path to a key to remove
        :return int:
        """
        self._logger.info(f"Deleting key: [{key_path}]")

        # check exists - to get rid of raising HTTP 404 error as an unwanted exception
        if not self.key_storage__exists(key_path):
            self._logger.debug(f"{key_path} does not exist")
            return requests.codes.not_found

        _req = self.__append_path_list(["storage", "keys"], key_path)
        return self.delete(_req, headers=self.headers, cookies=self.cookies).status_code

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
        self.__check_args(project=project)
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
        self.__check_args(project=project)
        _req = ["project", project, "config"]
        return self.get(_req, headers=self.headers, cookies=self.cookies).json()

    def project__update(self, project_configuration):
        """
        Create or update project
        :param BufferIO project_configuration: file-like object for project project_configuration
        :param str project_configuration: project project_configuration as read of 'project.properties' file
        :param dict project_configuration: project project_configuration dictionary {"propname":"propvalue", ...}
        :param _io.TextIOWrapper project_configuration: project project_configuration file-like object
        :return dict:
        """
        self._logger.info(" ".join([
            "Upating project configuration:",
            f"type of [project_configuration]: [{type(project_configuration)}]"]))

        self.__check_args(project_configuration=project_configuration)
        project_configuration = self._to_dict(project_configuration)
        project = project_configuration.get("project.name") or \
                project_configuration.get("name") or \
                project_configuration.get("config", dict()).get("project.name")

        self._logger.info(f"Project name: [{project}]")
        self.__check_args(project=project)

        # prepare project name and configuration
        if all(list(map(lambda _x: not project_configuration.get(_x), ["name", "config"]))):
            self._logger.debug(f"Both 'configuration' and 'name' absent in the Project configuration, appending all")
            project_configuration={"name": project, "config": project_configuration}
        elif project_configuration.get("config") and not project_configuration.get("name"):
            self._logger.debug(f"Project [{project}] configuration present but 'name' absent")
            project_configuration["name"] = project
        elif project_configuration.get("name") and not project_configuration.get("config"):
            raise ValueError(f"Project configuration is wrong: 'config' should be specified if 'name' key given")

        self._logger.log(5, f"Project configuration: {str(project_configuration)}")

        # if project exists - perform an update
        # create new one otherwise

        if self.project__exists(project):
            self._logger.info(f"Project [{project}] exists, performing an update...")
            return self.put(
                ["project", project, "config"],
                data=json.dumps(project_configuration.get("config")),
                headers=self.headers,
                cookies=self.cookies).json()

        self._logger.info(f"Project [{project}] does not exist, creating new one")
        return self.post("projects", data=json.dumps(project_configuration),
                         headers=self.headers, cookies=self.cookies).json()

    def project__delete(self, project):
        """
        Delete a project
        :param str project: project name
        :return int: status code
        """
        self._logger.info(f"Deleting project [{project}]")
        self.__check_args(project=project)

        # check exists - to get rid of raising HTTP 404 error as an unwanted exception
        if not self.project__exists(project):
            self._logger.debug(f"{project} does not exist")
            return requests.codes.not_found

        return self.delete(["project", project], headers=self.headers, cookies=self.cookies).status_code


    def scm__setup(self, project, scm_integration, scm_plugin_type, scm_configuration):
        """
        Setup SCM for a project
        :param str project: project name
        :param str scm_integration: one of: "import", "export"
        :param str scm_plugin_type: plugin to configure
        :param str scm_configuration: string with SCM parameters
        :param dict scm_configuration: dictionary with SCM parameters
        :param _io.TextIOWrapper scm_configuration: file-like object with SCM parameters opened in string mode
        :return dict:
        """
        self._logger.info(" ".join([
            "Upating project SCM configuration:",
            f"project: [{project}], scm_integration: [{scm_integration}], scm_plugin_type: [{scm_plugin_type}]",
            f"type of scm_configuration: [{type(scm_configuration)}]"]))

        # checking arguments
        self.__check_args(project=project, scm_integration=scm_integration,
                          scm_plugin_type=scm_plugin_type, scm_configuration=scm_configuration)
        scm_configuration = self._to_dict(scm_configuration)

        # configuration may be outside of a dict
        if not scm_configuration.get("config"):
            scm_configuration = {"config": scm_configuration}

        self._logger.log(5, f"Final [scm_configuration]: [{scm_configuration}]")

        _req = ["project", project, "scm", scm_integration, "plugin", scm_plugin_type, "setup"]

        return self.post(_req, headers=self.headers, cookies=self.cookies, data=json.dumps(scm_configuration)).json()

    def scm__enable(self, project, scm_integration, scm_plugin_type, enable=False):
        """
        Turn on/off SCM for a project
        :param str project: project name
        :param str scm_integration: one of: "import", "export"
        :param str scm_plugin_type: plugin to configure
        :param bool enable: disable if set to False, enable otherwise
        :return dict:
        """
        self._logger.info(
                " ".join([
                    'Enable' if enable else 'Disable',
                    f"SCM for project [{project}], scm_integration [{scm_integration}],",
                    f"scm_plugin_type [{scm_plugin_type}]"]))

        # checking arguments
        self.__check_args(project=project, scm_integration=scm_integration, scm_plugin_type=scm_plugin_type)

        _req = ["project", project, "scm", scm_integration, "plugin", scm_plugin_type, "enable" if enable else "disable"]

        return self.post(_req, headers=self.headers, cookies=self.cookies).json()

    def scm__get_action_inputs(self, project, scm_integration, scm_action):
        """
        Get items needed to be performed scm_actions on
        :param str project: project name
        :param str scm_integration: one of: "import", "export"
        :param str scm_action: scm_action to perform
        :return dict:
        """
        self._logger.info(" ".join([
            f"Get SCM scm_actions input list for project [{project}],",
            f"scm_integration [{scm_integration}], scm_action [{scm_action}]"]))

        # checking arguments
        self.__check_args(project=project, scm_integration=scm_integration, scm_action=scm_action)

        _req = ["project", project, "scm", scm_integration, "action", scm_action, "input"]

        return self.get(_req, headers=self.headers, cookies=self.cookies).json()

    def scm__action_perform(self, project, scm_integration, scm_action, scm_action_data):
        """
        SCM import/export all project items
        :param str project: project name
        :param str scm_integration: one of: "import", "export"
        :param str scm_action: scm_action to perform
        :param dict scm_action_data: what to do
        :return dict:
        """
        self._logger.info(" ".join([
            f"Perform SCM scm_actions for project [{project}],",
            f"scm_integration [{scm_integration}], scm_action [{scm_action}].",
            f"Action data: {scm_action_data}"]))

        if not scm_action_data:
            self._logger.info(f"Emtpy scm_action data, nothing to do")
            return dict()

        # checking arguments
        self.__check_args(project=project, scm_integration=scm_integration, scm_action=scm_action)

        _req = ["project", project, "scm", scm_integration, "action", scm_action]

        return self.post(_req, headers=self.headers, cookies=self.cookies, data=json.dumps(scm_action_data)).json()

    def scm__perform_all_actions(self, project, scm_integration, scm_action, commit_message=None):
        """
        SCM import/export all project items
        :param str project: project name
        :param str scm_integration: one of: "import", "export"
        :param str scm_action: scm_action to perform
        :param str commit_message: required to do "export-jobs" or so on
        :return dict:
        """
        # arguments checking is done in the sub-method
        self._logger.info(" ".join([
            f"Perform all SCM scm_actions for project [{project}],",
            f"scm_integration [{scm_integration}], scm_action [{scm_action}]"]))

        _scm_action_inputs = self.scm__get_action_inputs(project, scm_integration, scm_action)
        _rq_data = dict()

        if commit_message:
            _rq_data = {"input": {"message": commit_message}}

        # collect data basing on _scm_action_inputs
        # fields needed: 
        ## "jobs" - imprt/export for jobIds, actually useless
        ## "items" - itemId-s to be imported/exported
        ## "deleted" - itemIds to be deleted on "export" scm_integration
        ## "deletedJobs" - jobIds to be deleted on "import" scm_integration
        _section = f"{scm_integration}Items"
        self._logger.debug(f"Filtering and mapping section [{_section}]")
        _rq_data["jobs"] = list()
        # absence of "itemId" key on RunDeck response is a crime, exception should be raised
        _rq_data["items"] = list(map(lambda x: x["itemId"],
                                     list(filter(lambda x: not x.get("deleted"), _scm_action_inputs.get(_section)))))

        if scm_integration == "export":
            _rq_data["deleted"] = list(map(lambda x: x["itemId"], 
                                        list(filter(lambda x: x.get("deleted"), _scm_action_inputs.get(_section)))))
            _rq_data["deletedJobs"] = list()
        else:
            _rq_data["deleted"] = list()
            # addtional filter on empty "jobId" is necessary here since there may be no job associated yet
            # no need to do import/deletion then
            _rq_data["deletedJobs"] = list(filter(lambda x: bool(x),
                                        list(map(lambda x: x.get("job", dict()).get("jobId"),
                                           list(filter(lambda x: x.get("deleted"), _scm_action_inputs.get(_section)))))))

        self._logger.debug(f"Action data dict: {_rq_data}")
        return self.scm__action_perform(project, scm_integration, scm_action, _rq_data)


    def scm__status(self, project, scm_integration):
        """
        Get SCM plugin status for a project
        :param str project: project name
        :param str scm_integration: one of: "import", "export"
        :return dict:
        """
        self._logger.info(
                f"Get SCM status for project [{project}], scm_integration [{scm_integration}]")

        # checking arguments
        self.__check_args(project=project, scm_integration=scm_integration)

        _req = ["project", project, "scm", scm_integration, "status"]

        return self.get(_req, headers=self.headers, cookies=self.cookies).json()
