import json
import logging
import os
import tempfile
import time

from . import API
import posixpath


class Dbsm2API (API.HttpAPI):
    _env_prefix = 'DBSM2'

    def __init__(self, *args, **argv):
        logging.debug('Reached __init__')
        logging.debug('Calling base class constructor for availability of HttpAPI methods')

        super().__init__(*args, **argv)

        # auth token
        self.auth_token = None

        # delivery states or images in process
        self.waiting_states = ['UNKNOWN']

        # delivery states or images finished
        self.exit_states = ['FAILED', 'SUCCESS']

        # wait for state timeout
        self.wait_state_timeout = 1800

        # wait for state request interval
        self.wait_state_sleep = 30

        # oracle version
        self.oracle_version = '19.21.0.0.0'

        # oracle encoding
        self.oracle_encoding = 'AL32UTF8'

        # oracle edition
        self.oracle_edition = 'EE'

        # remove auth to stop requests overriding headers, do not raise exceptions on minor http errors
        self.web.auth = None
        self.raise_exception_high = 499

    def create_custom_image(self, version=None, distr_type=None, client_filter=None, client_code=None, schema_name=None):
        """
        Sends request to create custom image
        :param str version: version of product
        :param str distr_type: type of product
        :param str client_filter: client specific filter list
        :param str client_code: client code
        """
        logging.debug('Reached create_custom_image')
        logging.debug('version: [%s]' % version)
        logging.debug('distr_type: [%s]' % distr_type)
        logging.debug('client_filter: [%s]' % client_filter)
        logging.debug('client_code: [%s]' % client_code)
        logging.debug('schema_name: [%s]' % schema_name)
        logging.debug('oracle_version: [%s]' % self.oracle_version)
        logging.debug('oracle_encoding: [%s]' % self.oracle_encoding)
        logging.debug('oracle_edition: [%s]' % self.oracle_edition)

        if client_filter is None:
            logging.debug('received None client_filter, setting to empty string')
            client_filter = ''

        url = posixpath.join('api', 'v1', 'images', 'custom-cdt')
        headers = self.get_headers()
        params = {
            'image_type': 'CUSTOM',
            'product_type': distr_type.lower(),
            'product_version': version,
            'custom_attribute': client_code,
            'getver_filter': client_filter,
            'oracle_encoding': self.oracle_encoding,
            'oracle_version': self.oracle_version,
            'oracle_edition': self.oracle_edition,
            'schema_name': schema_name,
            'remap_tablespaces': 'true'
        }
        logging.debug('dumping request params')
        logging.debug(json.dumps(params, indent=4))
        r = self.post(url, headers=headers, json=params)
        return self.json_or_none(r)

    def download_file(self, image_id):
        """
        Downloads specified image to file
        :param str image_id: id of image to download
        :return: path to downloaded file
        """
        logging.debug('Reached download_file')
        logging.debug('image_id: [%s]' % image_id)
        logging.debug('Unsetting auth')
        headers = self.get_headers()
        url = posixpath.join('api', 'v1', 'images', image_id, 'download')
        logging.debug('url: [%s]' % url)
        tf = tempfile.NamedTemporaryFile()
        logging.debug('tf: [%s]' % tf)
        r = self.get(url, headers=headers, stream=True)
        for chunk in r.iter_content(chunk_size=8192):
            tf.write(chunk)
        tf.seek(0)
        return tf

    def get_audit(self, audit_id):
        """
        Requests audit record by record id
        :param str audit_id: id of audit record
        :return: audit record
        """
        logging.debug('Reached get_audit')
        logging.debug('audit_id: [%s]' % audit_id)
        headers = self.get_headers()
        url = posixpath.join('api', 'v1', 'audit', audit_id)
        r = self.get(url, headers=headers)
        return self.json_or_none(r)

    def get_headers(self):
        """
        """
        logging.debug('Reached get_headers')
        logging.debug('auth_token length: [%s]' % len(self.auth_token))
        headers = {'Accept': 'application/json; charset=utf-8', 'Authorization': f'Bearer {self.auth_token}'}
        return headers

    def get_image_details(self, image_id):
        """
        """
        logging.debug('Reached get_image_details')
        logging.debug('image_id: [%s]' % image_id)

        if image_id is None:
            logging.debug('received None image_id, returning None')
            return None

        headers = self.get_headers()
        url = posixpath.join('api', 'v1', 'images', image_id)
        r = self.get(url, headers=headers)
        return self.json_or_none(r)

    def search_image(self, version=None, distr_type=None):
        """
        searches for images, calls download
        :return: path to temp file, image data
        """
        logging.debug('Reached download_image')
        logging.debug('Unsetting auth')
        logging.debug('version = [%s]' % version)
        logging.debug('distr_type = [%s]' % distr_type)
        
        url = posixpath.join('api', 'v1', 'images')
        headers = self.get_headers()
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
        logging.debug('Dumping images data')
        logging.debug(json.dumps(images, indent=4))
        for image in images:
            image_id = image['id']
            image_name = image['name']
            oracle_version = image.get('oracle_version')
            customisation = image.get('customisation')
            logging.debug('checking images [%s]' % image_name)
            if oracle_version['oracle_edition'] == self.oracle_edition and customisation is None:
                logging.debug('image is enterprise edition')
                return image
        logging.error('No images found')
        return None

    def json_or_none(self, resp):
        """
        Returns requests response's json if status code is 200-299 or logs error and returns None
        :param requests.response resp: requests' response
        :return: requests.response.json or None
        """
        logging.debug('Reached json_or_none')
        status_code = resp.status_code
        if 200 <= status_code <= 299:
            logging.debug('[%s] status code received, trying to return json' % status_code)
            return resp.json()
        else:
            logging.error('[%s] status code received, assuming an error, returning None' % status_code)
        return None

    def login(self):
        """
        Obtain auth token
        """
        logging.debug('Reached login')
        username = os.getenv('DBSM2_USER')
        password = os.getenv('DBSM2_PASSWORD')
        login_data = {
            'grant_type': '',
            'username': username,
            'password': password,
            'scope': '',
            'client_id': '',
            'client_secret': ''
        }
        url = posixpath.join('api', 'v1', 'auth', 'access-token')
        resp = self.post(url, data=login_data)
        resp_data = resp.json()
        if resp.status_code == 200:
            token_type = resp_data['token_type']
            access_token = resp_data['access_token']
        else:
            logging.error('Server returned an error [%s] [%s]' % (resp.status_code, resp.text))
            raise API.HttpAPIError('login failed')
        logging.debug('token_type: [%s]' % token_type)
        logging.debug('access_token: [%s]' % access_token)
        self.auth_token = access_token
        return token_type, access_token

    def wait_for_image(self, audit_id):
        """
        Performs periodic requests for audit record.
        Returns audit record when it is in exit state.
        :param str audit_id: id of audit record
        :return: audit record
        """
        logging.debug('Reached wait_for_image')
        logging.debug('audit_id: [%s]' % audit_id)

        if not isinstance(self.wait_state_timeout, int):
            logging.debug('wait_state_timeout is not integer, attempting to convert')
            self.wait_state_timeout = int(self.wait_state_timeout)
        if not isinstance(self.wait_state_sleep, int):
            logging.debug('wait_state_sleep in not integer, attempting to convert')
            self.wait_state_sleep = int(self.wait_state_sleep)

        ela = 0
        st = int(time.time())
        audit = None

        while ela < self.wait_state_timeout:
            ela = int(time.time()) - st

            audit = self.get_audit(audit_id)

            if not audit:
                logging.error('get_audit returned None')
                return None

            status = audit['status']
            logging.debug('received audit object in status [%s]' % status)

            if status in self.exit_states:
                logging.debug('audit is in exit state, returning')
                return audit
            logging.debug('audit is not in exit state, sleeping [%s]' % self.wait_state_sleep)
            logging.debug('in wait: [%s] of [%s] seconds' % (ela, self.wait_state_timeout) )
            time.sleep(self.wait_state_sleep)
        logging.error('TIMEOUT waiting for image, returning None')
        return None

