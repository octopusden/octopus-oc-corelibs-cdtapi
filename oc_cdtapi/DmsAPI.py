import logging
import os
import re

from oc_cdtapi import API

class DmsAPIError(API.HttpAPIError):
    pass

class DmsAPI(API.HttpAPI):   # we use HttpAPI as a base class - the idea of HttpAPI is to use it as a skelet for new API clients
    """
    DmsAPI implementation
    """
    # do not forget about docstrings

    _env_prefix = 'DMS' # this automatically allows usage of DMS_* environment variables - everything is done in HttpAPI for you
    _env_token = '_TOKEN'
    _env_crs = '_CRS_URL' # now we have a separate Components Registry Service for components info obtaining

    def __init__(self, *args, **argv):
        """
        Initialiazing the parent class then loading the DMS API's bearer token
        """
        API.HttpAPI.__init__(self)
        self.crs_root = os.getenv(self._env_prefix + self._env_crs)
        token = os.getenv(self._env_prefix + self._env_token)
        if not self.crs_root:
            raise DmsAPIError("DMS API initialization failed. The components request url is not set")
        if token:
            self.headers = {"Authorization": "Bearer {}".format(token)}
        else:
            self.headers = {} # Empty headers dict is added for backwards-compatibility with bearer token functional

        if self.crs_root[-1] != '/': self.crs_root += '/'

    def re(self, req):
        """
        Re-defines default request formater, not to be called directly
        This forms request URL separated by / from string array
        """
        if len(req) == 0: return self.root
        return self.root + 'dms-service/rest/api/' + '/'.join(req)

        # directly accessing class variables outside the class itself is possible, but should be avoided
        # consider using setters/getters or storing state outside the class
    
    def crs_re(self, req):
        """
        Forming the correct URL for the DMS Components Registry Service
        """
        if len(req) == 0: return self.crs_root
        return self.crs_root + 'rest/api/' + '/'.join(req)

    def get_artifacts(self, component, version, ctype = None):
        """
        Gets list of artifacts of given component, version and type
        :param component: dms component name
        :param version:   dms version name
        :param ctype:     type of artifact. if not specified - query all known types
        :returns:         list of artifacts
        """
        assert bool(re.match('^[a-zA-Z0-9_-]*$', component)), "Component name must contain only latin letters, numbers, underscores and hyphens"
        assert bool(re.match('^[a-zA-Z0-9._-]*$', version)), "Version must contain only latin letters, numbers, underscores, hyphens and dots"
        logging.debug('Reached %s.get_artifacts', self.__class__.__name__)
        if ctype is None:
            types = self.get_types()
        else:
            assert bool(re.match('^[a-zA-Z0-9_-]*$', ctype)), "Component type must contain only latin letters, numbers, underscores and hyphens"
            types = [ ctype ]

        artifacts = []

        for t in types:
            req = ['2', 'component', component, 'version', version, t, 'list']
            artifacts += self.get(req, headers=self.headers, verify=False).json() # Why do you use write_to parameter instead of just using response object ?
            # also, requests has json parser, no need to re-invent it

        logging.debug('About to return an array of %d elements', len(artifacts)) # logging has its own format-string engine
        return artifacts


    def get_components(self):
        """
        Gets list of components known to DMS
        :returns: array of components
        """
        logging.debug('Reached %s.get_components', self.__class__.__name__)
        req = ['1', 'components']

        crs_request_url = self.crs_re(req)
        components = self.web.get(crs_request_url, verify=False).json()['components']
        logging.debug('About to return an array of %d elements', len(components))
        return components

    def get_gav(self, component, version, ctype, artifact, classifier=None):
        """
        Requests and forms gav for specified artifact
        :param component: component name
        :param version: version
        :param ctype:
        :param artifact:
        :param classifier:
        :returns: gav
        """
        assert bool(re.match('^[a-zA-Z0-9_-]+$', component)), "Component name have not to be empty and must contain only latin letters, numbers, underscores and hyphens"
        assert bool(re.match('^[a-zA-Z0-9\._-]+$', version)), "Version have not to be empty and must contain only latin letters, numbers, underscores, hyphens and dots"
        assert bool(re.match('^[a-zA-Z0-9_-]+$', ctype)), "Component type have not to be empty and must contain only latin letters, numbers, underscores and hyphens"
        assert bool(re.match('^[a-zA-Z0-9_-]+$', artifact)), "Artifact type have not to be empty and must contain only latin letters, numbers, underscores and hyphens"
        logging.debug('Reached %s.get_gav', self.__class__.__name__)
        logging.debug('component: {0}'.format(component))
        logging.debug('version: {0}'.format(version))
        logging.debug('artifact: {0}'.format(artifact))
        logging.debug('classifier: {0}'.format(classifier))
        req = ['1', 'component', component, 'version', version, ctype, artifact, 'gav']
        if classifier:
            assert bool(re.match('^[a-zA-Z0-9_-]+$', classifier)), "Non-empty classifier must contain only latin letters, hyphens and underscores"
            params = {'classifier': classifier}
        else:
            params = None

        gav = self.get(req, params, headers=self.headers).json()

        assert bool(re.match('^[a-zA-Z0-9\._-]+$', gav['groupId'])), "groupId have not to be empty and must contain only latin letters, numbers, underscores, hyphens and dots"
        assert bool(re.match('^[a-zA-Z0-9_-]+$', gav['artifactId'])), "artifactId have not to be empty and must contain only latin letters, numbers, underscores and hyphens"
        assert bool(re.match('^[a-zA-Z0-9\._-]+$', gav['version'])), "version have not to be empty and must contain only latin letters, numbers, underscores, hyphens and dots"
        assert bool(re.match('^[a-zA-Z0-9_-]+$', gav['packaging'])), "packaging have not to be empty and must contain only latin letters, hyphens and underscores"

        _gav = ':'.join( [gav['groupId'], gav['artifactId'], gav['version'], gav['packaging']] )
        if gav.get('classifier'):
            assert bool(re.match('^[a-zA-Z0-9_-]+$', gav['classifier'])), "non-empty classifier must contain only latin letters, hyphens and underscores"
            _gav = ':'.join([_gav, gav['classifier']])

        logging.debug('Formed gav: %s', _gav)

        return _gav


    def get_types(self): return ['notes', 'distribution', 'report', 'static', 'documentation']


    def get_versions(self, component):
        """
        fetches list of versions for specified component
        :param component: component name
        :returns: array of versions
        """
        assert bool(re.match('^[a-zA-Z0-9_-]*$', component)), "Component name must contain only latin letters, numbers, underscores and hyphens"
        logging.debug('Reached %s.get_versions', self.__class__.__name__)

        req = ['2', 'component', component, 'versions']

        versions = list(map(lambda x: x.get('version'), self.get(req, headers=self.headers).json().get('versions')))
        logging.debug('About to return an array of %d elements',len(versions))
        return versions


    def ping_dms(self):
        """
        sends a request to dms root
        :returns: server response
        """
        logging.debug('Reached %s.ping_dms', self.__class__.__name__)
        return self.get([], headers=self.headers).content

