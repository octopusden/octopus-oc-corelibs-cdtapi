import logging
import os
import re
import posixpath

from . import API


class DmsAPIError(API.HttpAPIError):
    pass


# we use HttpAPI as a base class - the idea of HttpAPI is to use it as a skelet for new API clients
class DmsAPI(API.HttpAPI):
    """
    DmsAPI implementation
    """
    # do not forget about docstrings

    # this automatically allows usage of DMS_* environment variables - everything is done in HttpAPI for you
    _env_prefix = 'DMS'
    _env_token = '_TOKEN'
    # for now we have a separate Components Registry Service for components info obtaining
    # TODO: refactor when it will be joined with base DMS API on the server-side
    _env_crs = '_CRS_URL'

    def __init__(self, *args, **argv):
        """
        Initialiazing the parent class then loading the DMS API's bearer token
        """

        super().__init__(*args, **argv)
        self.crs_root = os.getenv(self._env_prefix + self._env_crs)
        token = os.getenv(self._env_prefix + self._env_token)

        if not self.crs_root:
            raise DmsAPIError("DMS API initialization failed. The components request URL [%s] is not set" % (
                self._env_prefix + self._env_crs))

        if token:
            self.headers = {"Authorization": "Bearer {}".format(token)}
        else:
            # Empty headers dict is added for backwards-compatibility with bearer token functional
            self.headers = {}

    def __req(self, req):
        """
        Joining an URL to one posixpath-compatible
        :param str req: request, may be list of str
        :return str: joined req
        """
        if not req:
            return req

        if isinstance(req, list):
            logging.log(5, "re-formatting requested list [%s] URL to string" % ', '.join(req))
            req = posixpath.sep.join(req)

        return req


    def re(self, req):
        """
        Re-defines default request formater, not to be called directly
        This forms request URL separated by slash from string array
        :param req: list of str or str for sub-url
        :return str: full joined URL
        """

        if not req:
            return self.root

        # do not use 'urlparse.urljoin' here because it gives wrong result if 'root'
        # contains sub-path. Example:
        # urlparse.urljoin("https://exapmle.com:5400/c1/c2/c3", "c4/c5/c6")
        # gives 'https://exapmle.com:5400/c1/c2/c4/c5/c6'
        # while 'https://exapmle.com:5400/c1/c2/c3/c4/c5/c6' expected ('c3' missing)

        return posixpath.join(self.root, "dms-service", "rest", "api", self.__req(req))

    # directly accessing class variables outside the class itself is possible, but should be avoided
    # consider using setters/getters or storing state outside the class

    def crs_re(self, req):
        """
        Forming the correct URL for the DMS Components Registry Service
        :param req: list of str or str for sub-url
        :return str: full joined URL
        """
        if not req:
            return self.crs_root

        # see the note about 'urljoin' in 're' method - the same is applicable here

        return posixpath.join(self.crs_root, 'rest', 'api', self.__req(req))

    def get_artifacts(self, component, version, ctype=None):
        """
        Gets list of artifacts of given component, version and type
        :param component: dms component name
        :param version:   dms version name
        :param ctype:     type of artifact. if not specified - query all known types
        :returns:         list of artifacts
        """
        assert bool(re.match('^[a-zA-Z0-9_-]*$', component)
                    ), "Component name must contain only latin letters, numbers, underscores and hyphens"
        assert bool(re.match('^[a-zA-Z0-9._-]*$', version)
                    ), "Version must contain only latin letters, numbers, underscores, hyphens and dots"
        logging.debug('Reached %s.get_artifacts', self.__class__.__name__)

        if ctype is None:
            types = self.get_types()
        else:
            assert bool(re.match('^[a-zA-Z0-9_-]*$', ctype)
                        ), "Component type must contain only latin letters, numbers, underscores and hyphens"
            types = [ctype]

        artifacts = []

        for t in types:
            req = ['2', 'component', component, 'version', version, t, 'list']

            # Why do you use write_to parameter instead of just using response object ?
            # also, requests has json parser, no need to re-invent it
            artifacts += self.get(req, headers=self.headers, verify=False).json()

        # logging has its own format-string engine
        logging.debug('About to return an array of %d elements', len(artifacts))

        return artifacts

    def get_components(self):
        """
        Gets list of components known to DMS
        :returns: array of components
        """
        logging.debug('Reached %s.get_components', self.__class__.__name__)
        req = ['1', 'components']

        crs_request_url = self.crs_re(req)
        components = self.web.get(crs_request_url, verify=False).json().get('components', list())
        logging.debug('About to return an array of %d elements', len(components))

        return components

    def get_gav(self, component, version, ctype, artifact, classifier=None):
        """
        Requests and forms gav for specified artifact
        :param str component: component name
        :param str version: version
        :param str ctype:
        :param str artifact:
        :param str classifier:
        :returns str: gav
        """
        assert bool(re.match('^[a-zA-Z0-9_-]+$', component)
                    ), "Component name have not to be empty and must contain only latin letters, numbers, underscores and hyphens"
        assert bool(re.match('^[a-zA-Z0-9\._-]+$', version)
                    ), "Version have not to be empty and must contain only latin letters, numbers, underscores, hyphens and dots"
        assert bool(re.match('^[a-zA-Z0-9_-]+$', ctype)
                    ), "Component type have not to be empty and must contain only latin letters, numbers, underscores and hyphens"
        assert bool(re.match('^[a-zA-Z0-9_-]+$', artifact)
                    ), "Artifact type have not to be empty and must contain only latin letters, numbers, underscores and hyphens"
        logging.debug('Reached %s.get_gav', self.__class__.__name__)
        logging.debug('component: {0}'.format(component))
        logging.debug('version: {0}'.format(version))
        logging.debug('artifact: {0}'.format(artifact))
        logging.debug('classifier: {0}'.format(classifier))
        req = ['1', 'component', component, 'version', version, ctype, artifact, 'gav']

        params = None

        if classifier:
            assert bool(re.match('^[a-zA-Z0-9_-]+$', classifier)
                        ), "Non-empty classifier must contain only latin letters, hyphens and underscores"
            params = {'classifier': classifier}

        gav = self.get(req, params, headers=self.headers).json()

        assert bool(re.match('^[a-zA-Z0-9\._-]+$', gav['groupId'])
                    ), "groupId have not to be empty and must contain only latin letters, numbers, underscores, hyphens and dots"
        assert bool(re.match('^[a-zA-Z0-9_-]+$', gav['artifactId'])
                    ), "artifactId have not to be empty and must contain only latin letters, numbers, underscores and hyphens"
        assert bool(re.match('^[a-zA-Z0-9\._-]+$', gav['version'])
                    ), "version have not to be empty and must contain only latin letters, numbers, underscores, hyphens and dots"
        assert bool(re.match('^[a-zA-Z0-9_-]+$', gav['packaging'])
                    ), "packaging have not to be empty and must contain only latin letters, hyphens and underscores"

        _gav = ':'.join(list(map(lambda x: gav[x], ['groupId', 'artifactId', 'version', 'packaging'])))

        if gav.get('classifier'):
            assert bool(re.match('^[a-zA-Z0-9_-]+$', gav['classifier'])
                        ), "non-empty classifier must contain only latin letters, hyphens and underscores"
            _gav = ':'.join([_gav, gav['classifier']])

        logging.debug('Formed gav: %s', _gav)

        return _gav

    def get_types(self): 
        return ['notes', 'distribution', 'report', 'static', 'documentation']

    # Some DMS implementations may return a result without 'status' key
    # 'None' value added to defaults for this case
    def get_versions(self, component, version_status=['RELEASE', None]):
        """
        fetches list of versions for specified component
        :param str component: component name
        :returns list: versions
        """

        assert bool(re.match('^[a-zA-Z0-9_-]*$', component)
                    ), "Component name must contain only latin letters, numbers, underscores and hyphens"

        logging.debug('Reached %s.get_versions', self.__class__.__name__)

        req = ['2', 'component', component, 'versions']

        _result = self.get(req, headers=self.headers).json().get('versions')
        # filter versions by-type
        if version_status:
            logging.debug(f"Filtering versions")

            if isinstance(version_status, str):
                logging.debug(f"Converting [{version_status}] to list")
                version_status = [version_status]

            _result = list(filter(lambda x: x.get('status') in version_status, _result))

        _result = list(map(lambda x: x.get('version'), _result))
        logging.debug('About to return an array of %d elements', len(_result))

        return _result

    def ping_dms(self):
        """
        sends a request to dms root
        :returns: server response
        """
        logging.debug('Reached %s.ping_dms', self.__class__.__name__)

        return self.get([], headers=self.headers).content


class DmsAPIv3(API.HttpAPI):
    """
    DMS API v.3 implementation
    """
    _env_prefix = 'DMS'

    def __req(self, req):
        """
        Joining an URL to one posixpath-compatible
        :param str req: request, may be list of str
        :return str: joined req
        """
        if not req:
            logging.debug("Empty request")
            return ""

        if isinstance(req, list):
            logging.debug(f"re-formatting requested list {req} URL to string")
            req = posixpath.sep.join(req)

        logging.debug(f"Request to return: {req}")

        return req

    def re(self, req):
        """
        Re-defines default request formater, not to be called directly
        This forms request URL separated by slash from string array
        :param req: list of str or str for sub-url
        :return str: full joined URL
        """

        if not req:
            logging.debug("Empty request")
            return self.root

        # do not use 'urlparse.urljoin' here because it gives wrong result if 'root'
        # contains sub-path. Example:
        # urlparse.urljoin("https://exapmle.com:5400/c1/c2/c3", "c4/c5/c6")
        # gives 'https://exapmle.com:5400/c1/c2/c4/c5/c6'
        # while 'https://exapmle.com:5400/c1/c2/c3/c4/c5/c6' expected ('c3' missing)
        _req = posixpath.join(self.root, "dms-service", "rest", "api", "3", self.__req(req)).rstrip(posixpath.sep)
        logging.debug(f"Returning request URL: {_req}")

        return _req

    def ping_dms(self):
        """
        sends a request to dms root
        :return requests.Response: server response
        """
        logging.debug("Sending DMS ping")

        return self.get([]).content

    def get_artifacts(self, component, version, ctype=None):
        """
        Get list of artifacts of given component, version and type
        :param str component: DMS component name
        :param str version: DMS version name
        :param str ctype: type of artifact if not specified - query all known types
        :return list: artifacts
        """
        logging.debug(f"Requested artifacts for [{component}], version {version}, type [{ctype}])")

        _result = self.get(['components', component, 'versions', version, 'artifacts'], 
                           params=None if not ctype else {"type": ctype}).json().get('artifacts', list())

        logging.debug(f'About to return an array of [{len(_result)}] elements')

        return _result

    def get_components(self):
        """
        Gets list of components known to DMS
        :return list: components
        """
        logging.debug("Requested components list")
        _result = self.get('components').json().get('components', list())
        logging.debug(f"About to return array of [{len(_result)}] elements")

        return _result

    # 'get_gav' is not supported in v.3 since 'DEB' and 'RPM' packages do not have GAVs by-default

    # Some DMS implementations may return a result without 'status' key
    # 'None' value added to defaults for this case
    def get_versions(self, component, version_status=['RELEASE', None]):
        """
        Return list of versions for component
        :param str component: component name
        :param list version_status: version statuses to filter, possible: ['RELEASE', 'RC']
        :return list: versions
        """
        logging.debug(f"Requested versions for [{component}], version statuses: [{version_status}]")
        _result = self.get(['components', component, 'versions']).json().get("versions", list())
        logging.debug(f"Got array of [{len(_result)}] elements")

        if version_status:
            logging.debug(f"Filtering versions")

            if isinstance(version_status, str):
                logging.debug(f"Converting [{version_status}] to list")
                version_status = [version_status]

            _result = list(filter(lambda x: x.get('status') in version_status, _result))

        _result = list(map(lambda x: x.get('version'), _result))
        logging.debug(f"About to return array of [{len(_result)}] elements")

        return _result

    # to be used instead of 'get_gav' and downloading from artifactory
    def download_component(self, component, version, artifact_id, write_to=None):
        """
        Download a distributive component for a version given
        :param str component:
        :param str version:
        :param int artifact_id:
        :param _io.BufferIO write_to: file-like object (binary mode) to write artifact content to
        """

        logging.debug(f"Downloading {component}/{version}/{artifact_id} to [{write_to}]")
        return self.get(['components', component, 'versions', version, 'artifacts', str(artifact_id), 'download'], 
                        stream=True, write_to=write_to)

    def download_artifact(self, artifact_id, write_to=None):
        """
        Download artifact by id
        :param int artifact_id: DMS artifact id
        :param write_to: file-like object to write to
        """
        logging.debug(f"Downloading [{artifact_id}] to [{write_to}]")
        return self.get(['artifacts', str(artifact_id), 'download'], stream=True, write_to=write_to)

    def get_artifact_info(self, component, version, artifact_id):
        """
        Get artifact information by its ID
        :param str component:
        :param str version:
        :param int artifact_id:
        :return dict:
        """
        logging.debug(f"Getting artifact information: [{artifact_id}]")
        return self.get(['components', component, 'versions', version, 'artifacts', str(artifact_id)]).json()
