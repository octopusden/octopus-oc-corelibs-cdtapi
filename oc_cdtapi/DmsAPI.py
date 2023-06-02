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

        # TODO: re-factor when Python2 support will be deprecated
        super(DmsAPI, self).__init__(*args, **argv)
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

    def get_versions(self, component):
        """
        fetches list of versions for specified component
        :param str component: component name
        :returns list: versions
        """

        assert bool(re.match('^[a-zA-Z0-9_-]*$', component)
                    ), "Component name must contain only latin letters, numbers, underscores and hyphens"

        logging.debug('Reached %s.get_versions', self.__class__.__name__)

        req = ['2', 'component', component, 'versions']

        versions = list(map(lambda x: x.get('version'), self.get(req, headers=self.headers).json().get('versions')))
        logging.debug('About to return an array of %d elements', len(versions))

        return versions

    def ping_dms(self):
        """
        sends a request to dms root
        :returns: server response
        """
        logging.debug('Reached %s.ping_dms', self.__class__.__name__)

        return self.get([], headers=self.headers).content
