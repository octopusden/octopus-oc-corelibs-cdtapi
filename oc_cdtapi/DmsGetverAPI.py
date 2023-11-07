import json
import logging
import os
import tempfile
import time

from . import API
import posixpath


class DmsGetverAPI (API.HttpAPI):
    # prefix for credentials environment variables used by HttpAPI
    _env_prefix = 'DMS'

    def __init__(self, *args, **argv):
        logging.debug('Reached __init__')
        logging.debug('Calling base class constructor for availability of HttpAPI methods')

        # TODO: re-factor when Python2 support will be deprecated
        super(DmsGetverAPI, self).__init__(*args, **argv)

        # delivery states in process
        self.waiting_states = ['INITIATED', 'PROCESSING', 'QUEUED']

        # delivery states finished
        self.exit_states = ['READY', 'FAILED', 'SUCCESS']

        # wait for state timeout
        self.wait_state_timeout = 1000

        # wait for state request interval
        self.wait_state_sleep = 30

        # oracle version
        self.oracle_version = '19.16.0.0.0'

        # oracle encoding
        self.oracle_encoding = 'AL32UTF8'

        # oracle edition
        self.oracle_edition = 'EE'

    def create_custom_image(self, version=None, distr_type=None, client_filter=None, client_code=None, auth_token=None):
        """
        """
        logging.debug('Reached create_custom_image')
        logging.debug('version: [%s]' % version)
        logging.debug('distr_type: [%s]' % distr_type)
        logging.debug('client_filter: [%s]' % client_filter)
        logging.debug('client_code: [%s]' % client_code)
        logging.debug('auth_token: [%s]' % auth_token)

        self.web.auth = None
        url = posixpath.join('api', 'v1', 'images', 'custom-cdt')
        headers = self.get_headers_by_token(auth_token)
        params = {
            'image_type': 'CUSTOM',
            'product_type': distr_type.lower(),
            'product_version': version,
            'custom_attribute': client_code,
            'getver_filter': client_filter,
            'oracle_encoding': self.oracle_encoding,
            'oracle_version': self.oracle_version,
            'oracle_edition': self.oracle_edition,
            'remap_tablespaces': 'true'
        }
        resp = self.post(url, headers=headers, json=params)
        return resp.json()

    def create_distr_request(self, version=None, source_version=None, distr_type=None, client_filter=None):
        """
        Creates a new distribution request
        :param str version: required version e.g. 03.44.30.55
        :param str distr_type: distribution type 
        :param client_filter: a set of software components 
        :return: distribution state info as returned by dms
        """
        logging.debug('Reached create_distr_request')

        distr_state_info = self._create_distr_request_int(
            version=version, source_version=source_version, distr_type=distr_type, client_filter=client_filter)

        return distr_state_info

    def download_file(self, image_id, auth_token):
        """
        """
        logging.debug('Reached download_file')
        logging.debug('image_id: [%s]' % image_id)
        logging.debug('auth_token: [%s]' % auth_token)
        logging.debug('Unsetting auth')
        self.web.auth = None
        headers = self.get_headers_by_token(auth_token)
        url = posixpath.join('api', 'v1', 'images', image_id, 'download')
        logging.debug('url: [%s]' % url)
        tf = tempfile.NamedTemporaryFile(delete=False)
        tfn = tf.name
        logging.debug('tf: [%s]' % tfn)
        r = self.get(url, headers=headers, stream=True)
        for chunk in r.iter_content(chunk_size=8192):
            tf.write(chunk)
        tf.seek(0)
        return tfn

    def get_audit(self, audit_id, auth_token):
        """
        """
        logging.debug('Reached get_audit')
        logging.debug('audit_id: [%s]' % audit_id)
        logging.debug('auth_token: [%s]' % auth_token)
        self.web.auth = None
        headers = self.get_headers_by_token(auth_token)
        url = posixpath.join('api', 'v1', 'audit', audit_id)
        r = self.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        else:
            return None

    def get_headers_by_token(self, auth_token):
        """
        """
        logging.debug('Reached get_headers_by_token')
        logging.debug('auth_token: [%s]' % auth_token)
        headers = {'Accept': 'application/json; charset=utf-8', 'Authorization': f'Bearer {auth_token}'}
        logging.debug('About to return: [%s]' % headers)
        return headers

    def search_image(self, version=None, source_version=None, distr_type=None, client_filters=None, auth_token=None):
        """
        searches for images, calls download
        :return: path to temp file, image data
        """
        logging.debug('Reached download_image')
        logging.debug('Unsetting auth')
        self.web.auth = None
        if not auth_token:
            logging.error('No auth token provided, giving up')
            return None
        logging.debug('version = [%s]' % version)
        logging.debug('source_version = [%s]' % source_version)
        logging.debug('distr_type = [%s]' % distr_type)
        logging.debug('client_filters = [%s]' % client_filters)
        logging.debug('auth_token length = [%s]' % len(auth_token))
        
        url = posixpath.join('api', 'v1', 'images')
        headers = self.get_headers_by_token(auth_token)
        params = {
            'strict_filters': 'true',
            'product_type': distr_type.lower(),
            'product_version': version,
            'product_release_stage': 'release',
            'remap_tablespaces': 'true'
        }
        resp = self.get(url, headers=headers, params=params)
        if not resp.status_code == 200:
            logging.error('Server returned an error [%s] [%s]' % (resp.status_code, resp.text))
            return None
        images = resp.json()['items']
        logging.debug('found [%s] images' % len(images))
        for image in images:
            image_id = image['id']
            image_name = image['name']
            oracle_version = image['oracle_version']
            logging.debug('checking images [%s]' % image_name)
            if oracle_version['oracle_edition'] == 'EE':
                logging.debug('image is enterprise edition')
                return image
        logging.error('No images found')
        return None

    def get_distr(self, distr_id, distr_option):
        """
        Fetches distribution from dms
        :param str distr_id: distribution id
        :return tuple(distr, distr_state_info): distribution fetched from dms or None on error, distribution info
        """
        logging.debug('Reached get_distr')
        logging.debug('Distr id [%s]' % distr_id)
        logging.debug('Distr option [%s]' % distr_option)
        distr = None

        distr_state_info = self.get_distr_state_info_byid(distr_id, distr_option)
        if distr_state_info['state'] != 'READY':
            logging.debug('Distribution [%s] is in not ready state [%s]' % (
                distr_id, distr_state_info['state']))
        else:
            logging.debug('Distribution [%s] is in ready state, downloading' % distr_id)
            url = posixpath.join('dms-getver', 'distribution', 'id:%s' % distr_id, 'download')
            logging.debug('Getting from [%s]' % url)
            logging.debug('Requesting [%s]' % distr_state_info['fileName'])
            distr_resp = self.get(url)
            if distr_resp.status_code != 200:
                logging.debug('DMS returned an error response [%s] while getting [%s]' % (
                    distr_resp.status_code, url))
            else:
                distr = distr_resp.content
                logging.debug('Fetched [%s] bytes from [%s]' % (len(distr), url))

        return distr, distr_state_info

    def get_distr_state_info(self,  version=None, source_version=None, distr_type=None, client_filter=None):
        """
        Requests distribution state info from dms
        parameters description see in create_distr_request
        """
        logging.debug('Reached get_distr_state_info')

        url, parms = self._get_distr_state_url(
            version=version, source_version=source_version, distr_type=distr_type, client_filter=client_filter)
        distr_state_info = self._get_distr_state_info_int(url, parms)

        return distr_state_info

    def get_distr_state_info_byid(self, distr_id, distr_option):
        """
        Requests distribution state info from dms
        :param str distr_id: distributive ID (digits-as-string)
        :param str distr_option: additional distributive option
        :return distr_state_info: distributive state information
        """
        logging.debug('Reached get_distr_state_info_byid')

        if distr_option == 'full':
            logging.debug('Full distr info requested')
            url = posixpath.join('dms-getver', 'rest', 'api', '1', 'distribution', 'id:%s' % distr_id)
        else:
            logging.debug('Diff distr info requested')
            url = posixpath.join('dms-getver', 'rest', 'api', '1', 'distribution-difference', 'id:%s' % distr_id)

        distr_state_info = self._get_distr_state_info_int(url)

        return distr_state_info

    def get_dms_gav(self, distr_id, distr_option):
        """
        Requests gav by distribution id
        :param str distr_id: distributive ID (digits-as-string)
        :param str distr_option: additional distributive option
        :return str: GAV, or None if not found
        """
        logging.debug('Reached get_dms_gav')
        logging.debug('Request for gav for [%s] distr id [%s]' % (
            distr_option, distr_id))

        if distr_option == 'full':
            url = posixpath.join('dms-getver', 'rest', 'api', '1', 'distribution', 'id:%s' % distr_id, 'gav')
        else:
            url = posixpath.join('dms-getver', 'rest', 'api', '1', 'distribution-difference', 'id:%s' % distr_id, 'gav')

        resp = self.get(url)

        if resp.status_code == 200:
            logging.debug('OK response from dms-getver')
            gav = resp.json()
            # we have to raise an exception if anything were not returned
            # it is the cause to rid of 'get' method usage
            gav_text = ':'.join(list(map(lambda x: gav[x], [
                'groupId', 'artifactId', 'version', 'packaging'])))

            logging.debug('Returning [%s]' % gav_text)
        else:
            logging.debug('Error response [%s] from dms-getver' % resp.status_code)
            gav_text = None
            logging.debug('Returning None')

        return gav_text

    def get_dms_log(self, distr_id, distr_option):
        """
        Retrieve dms log
        :param str distr_id: distributive ID (digits-as-string)
        :param str distr_option: additional distributive option
        :return str: DMS log, or None if no logs found or response error
        """
        logging.debug('Reached get_dms_log')
        logging.debug('Request for log of processing distr [%s]' % distr_id)

        url = self.get_dms_log_url(distr_id, distr_option)

        log = None
        resp = self.get(url)
        status_code = resp.status_code
        logging.debug('Response status code: [%s]' % status_code)

        if status_code != 200:
            logging.debug('Error response from dms')
        else:
            log = resp.text

        return log

    def get_dms_log_url(self, distr_id, distr_option):
        """
        Prepare log URL
        :param str distr_id: distributive ID (digits-as-string)
        :param str distr_option: additional distributive option
        :return str: DMS log URL for further requesting
        """
        logging.debug('Reached get_dms_log_url')
        logging.debug('Request for url for [%s] distr [%s]' % (distr_option, distr_id))

        url = posixpath.join('dms-getver', 'rest', 'api', '1', 'distribution%s' % (
            "-difference" if distr_option != "full" else ""), 'id:%s' % distr_id, 'log')

        logging.debug('url for log request: [%s]' % url)

        return url

    def login(self):
        """
        Obtain auth token
        """
        logging.debug('Reached login')
        username = os.getenv('DMS_USER')
        password = os.getenv('DMS_PASSWORD')
        login_data = {
            'grant_type': '',
            'username': username,
            'password': password,
            'scope': '',
            'client_id': '',
            'client_secret': ''
        }
        rh = self.raise_exception_high
        self.raise_exception_high = 499
        url = posixpath.join('api', 'v1', 'auth', 'access-token')
        try:
            resp = self.post(url, data=login_data)
            resp_data = resp.json()
            if resp.status_code == 200:
                token_type = resp_data['token_type']
                access_token = resp_data['access_token']
            else:
                logging.debug('Server returned an error [%s] [%s]' % (resp.status_code, resp.text))
                return None
        except:
            raise
        logging.debug('token_type: [%s]' % token_type)
        logging.debug('access_token: [%s]' % access_token)
        self.raise_exception_high = rh
        return token_type, access_token


    def wait_for_image(self, audit_id, auth_token):
        """
        """
        logging.debug('Reached wait_for_image')
        logging.debug('audit_id: [%s]' % audit_id)
        logging.debug('auth_token: [%s]' % auth_token)
        self.web.auth = None
        ela = 0
        st = int(time.time())
        audit = None

        while ela < self.wait_state_timeout:
            ela = int(time.time()) - st
            audit = self.get_audit(audit_id, auth_token)

            if not audit:
                logging.error('get_audit returned None')
                return None

            status = audit['status']
            logging.debug('received audit object in status [%s]' % status)

            if status in self.exit_states:
                logging.debug('audit is in exit state, returning')
                return audit

        return None

    def wait_for_state(self, distr_id, distr_option):
        """
        Wait until either distr gets into an exit state or a timeout occurs
        States and timeouts are defined in __init__
        :param str distr_id: distributive ID (digits-as-string)
        :param str distr_option: additional distributive option
        :return distr_state_info: distributive information after wait
        """
        logging.debug('Reached wait_for_state')
        ela = 0
        st = int(time.time())
        distr_state_info = {}
        distr_state_info['state'] = 'TIMEOUT'

        while ela < self.wait_state_timeout:
            ela = int(time.time()) - st
            dsi = self.get_distr_state_info_byid(distr_id, distr_option)
            state = dsi['state']

            if not state in self.waiting_states:
                logging.debug('Distr [%s] is in exit state [%s]' % (distr_id, state))
                distr_state_info = dsi
                break

            logging.debug('Distr [%s] is in waiting state [%s]' % (distr_id, state))
            logging.debug('Retrying in [%s] sec., [%s] of [%s] sec. in wait' % (
                self.wait_state_sleep, ela, self.wait_state_timeout))

            time.sleep(self.wait_state_sleep)

        return distr_state_info

    def _create_distr_request_int(self, version=None, source_version=None, distr_type=None, client_filter=None):
        """
        Creates a new distribution request
        :param str versoin: version required
        :param str source_version: source version for diff-type distributives
        :param str distr_type: type of distributive requested
        :param client_filter: components to filter, may be empty
        :return distr_state_info: or None on error
        """

        logging.debug('Reached _create_distr_request_int')
        logging.debug('version = [%s]' % version)
        logging.debug('source_version = [%s]' % source_version)
        logging.debug('distr_type = [%s]' % distr_type)

        if client_filter:
            logging.debug('client_filter length = [%s]' % len(client_filter))
        else:
            logging.debug('Filters not specified')
            client_filter = ''

        distr_state_info = {}
        req_parm = {}
        req_parm['product'] = distr_type

        if source_version:
            logging.debug('Diff distribution requested')
            url = posixpath.join('dms-getver', 'rest', 'api', '1', 'distribution-difference')
            req_parm['initialVersion'] = source_version
            req_parm['targetVersion'] = version
            req_parm['initialFilters'] = client_filter
            req_parm['targetFilters'] = client_filter
        else:
            logging.debug('Full distribution requested')
            url = posixpath.join('dms-getver', 'rest', 'api', '1', 'distribution')
            req_parm['version'] = version
            req_parm['filter'] = client_filter

        logging.debug('request parameters: [%s]' % json.dumps(req_parm, indent=4))
        resp = self.post(url, json=req_parm)

        # we shold have been expecting 202 here, but it's 200 somehow
        if resp.status_code != 200:
            logging.debug('DMS responds with unexpected status code [%s]' % resp.status_code)
            logging.debug('DMS response body: %s' % resp.text)
            distr_state_info['id'] = None
            distr_state_info['state'] = 'HTTP/%s' % resp.status_code
        else:
            distr_state_info = resp.json()

        distr_state = distr_state_info['state']
        distr_id = distr_state_info['id']

        if distr_state and distr_id:
            logging.debug('Created dist id [%s] in state [%s]' % (distr_id, distr_state))
            distr_state_info = self._normalize_dsi(distr_state_info)

        return distr_state_info

    def _dumb_404(self, resp):
        """
        This is to distinguish a server 404 from an application 404 (which should have been 200)
        :param resp: response to check
        :return bool: do we have to return 404 or not
        """
        logging.debug('Reached _dumb_404')

        try:
            j = resp.json()
        except ValueError as e:
            logging.debug('Failed to get json from dms response, returning False')
            return False

        if j.get('code') == 'DMS-GETVER-40001':
            logging.debug('Found a "dms not found" response code, returning True')
            return True

        logging.debug('Json response processed, but no "dms not found" code detected, returning False')
        return False

    def _get_distr_state_info_int(self, url, parms=None):
        """
        Requests and returns distr state
        states known so far: INITIATED, PROCESSING, FAILED, READY. + 
        NOTFOUND set by this method upon http/404 and TIMEOUT set by wait_for_state
        :param str url: URL to request
        :param dict params: additional request parameters
        :return requests.Response: 
        """
        logging.debug('Reached _get_distr_state_info_int')
        logging.debug('URL = [%s]' % url)

        try:
            if 'id:' in url:
                resp = self.get(url, params=parms)
            else:
                resp = self.post(url, json=parms)
        except API.HttpAPIError as e:
            resp = e.resp

        distr_state_info = {}

        # bad status
        if resp.status_code != 200:
            logging.debug('DMS reponds with status code [%s]' % resp.status_code)

            if resp.status_code == 404 and self._dumb_404(resp):
                distr_state_info['state'] = 'NOTFOUND'
                distr_state_info['id'] = None
            else:
                distr_state_info['state'] = 'HTTP/%s' % resp.status_code
                distr_state_info['id'] = None

        # ok status
        else:
            distr_state_info = resp.json()

        distr_id = distr_state_info['id']
        distr_state = distr_state_info['state']

        if distr_state and distr_id:
            distr_state_info = self._normalize_dsi(distr_state_info)
            logging.debug('Found dist id [%s] in state [%s]' % (distr_id, distr_state))

        return distr_state_info

    def _get_distr_state_url(self, version, source_version=None, distr_type=None, client_filter=None):
        """
        forms an url to be used to get distr state info or request new distribution
        :param str versoin: version required
        :param str source_version: source version for diff-type distributives
        :param str distr_type: type of distributive requested
        :param client_filter: components to filter, may be empty
        :return tuple(str, dict): URL for further request, parameters for the request
        """
        logging.debug('Reached _get_distr_state_url')
        logging.debug('Request for url version [%s], type [%s], src_ver [%s]' % (version, distr_type, source_version))

        if source_version:
            url = posixpath.join('dms-getver', 'rest', 'api', '1', 'distribution-difference')
            parms = {'initialFilters': client_filter, 'initialVersion': source_version,
                     'product': distr_type, 'targetFilters': client_filter, 'targetVersion': version}
        else:
            url = posixpath.join('dms-getver', 'rest', 'api', '1', 'distribution')
            parms = {'filter': client_filter, 'product': distr_type, 'version': version}

        logging.debug('URL=[%s]' % url)

        return url, parms

    def _normalize_dsi(self, distr_state_info):
        """
        Normalize scattered output from different endpoints
        :param dict distr_state_info: distributive state information
        :return dict: normalized distr_state_info
        """

        logging.debug('Reached _normalize_dsi')

        if 'initialFilters' in distr_state_info.keys():
            logging.debug('Diff distribution meta-info detected, add distOption=diff, filter, version')
            distr_state_info['distOption'] = 'diff'
            distr_state_info['filter'] = distr_state_info['targetFilters']
            distr_state_info['version'] = distr_state_info['targetVersion']
        else:
            logging.debug('Full distribution meta-info detected, only add distOption=full')
            distr_state_info['distOption'] = 'full'

        return distr_state_info
