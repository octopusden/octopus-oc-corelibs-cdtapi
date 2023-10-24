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
        """
        if not self._api_version:
            self._get_api_version()

        return self._api_version

    @property
    def headers(self):
        """
        Return default headers basing on authorization method
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

    def re(self, req):
        """
        Preprocess request URL
        """
        if not isinstance(req, list): 
            req = list(filter(lambda x: x, posixpath.split(req)))

        req = ["api", str(self.api_version)] + req
        return super().re(req)

    def key_storage__list_keys(self, path=None):
        """
        list internal KeyStorage content
        :param str path: internal path to list
        """
        logging.debug(f"path: {path}")
        _req = ["storage", "keys"]

        if path:
            if isinstance(path, str):
                path = list(filter(lambda x: x, posixpath.split(path)))

            self._logger.debug(f"path: {path}")
            _req += path
            self._logger.debug(f"_req: {_req}")

        _resp = self.get(_req, headers=self.headers, cookies=self.cookies)
        return _resp.json()

    def key_storage__key_exists(self, path):
        """
        Check if key exists
        :param str path: internal Rundeck path to the key to check
        """
        try:
            self.key_storage__list_keys(path)
        except HttpAPIError as _e:
            if _e.code == requests.codes.not_found:
                return False

            raise

        return True
