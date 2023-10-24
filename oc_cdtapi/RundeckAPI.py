#!/usr/bin/env python3

# implementation of Rundeck REST API calls

import sys

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
        :return dict:
        """
        logging.debug(f"path: {path}")
        _req = ["storage", "keys"]

        if path:
            _req =self.__append_path_list(_req, path)

        _resp = self.get(_req, headers=self.headers, cookies=self.cookies)
        return _resp.json()

    def key_storage__exists(self, path):
        """
        Check if key exists
        :param str path: internal Rundeck path to the key to check
        """
        try:
            self.key_storage__list(path)
        except HttpAPIError as _e:
            if _e.code == requests.codes.not_found:
                return False

            raise

        return True

    def key_storage__upload(self, path, key_type, content):
        """
        Create or update a key
        :param str path: internal KeyStorage path
        :param str key_type: type of key. May be set as 'application/xxx' directly or via aliases supported:
                             private, public, password
        :param bytes content: bytes array provides a password
        """
        if not path:
            raise ValueError("Key path is mandatory")

        if not key_type:
            raise ValueError("Key type is mandatory")

        if not content:
            raise ValueError("Key content is mandatory")

        # if key exists then we should update its content using PUT method
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
        _headers["Content-type"] = __keytype_map.get(key_type, key_type)

        _method = self.put if self.key_storage__exists(path) else self.post
        _method(req=_req, headers=_headers, data=content)
