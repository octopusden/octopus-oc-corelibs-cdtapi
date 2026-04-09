import doctest
import os
import re
from xml.etree import ElementTree
import posixpath
import logging

import requests
from .API import HttpAPI, HttpAPIError

import sys
if sys.version_info.major == 2:
    strtype = basestring
elif sys.version_info.major == 3:
    strtype = str

# Nexus url should include "/nexus" ending
# GAV has the following format: groupid:artifactid:version[:packaging[:clasifier]]
# This interface should be considered low-level

class NexusAPIError(HttpAPIError):
    def __str__(self):
        return 'Nexus error: ' + self.text + ': Code ' + str(self.code) + ' ' + self.url


def parse_gav(gav, relaxed=False):
    """
    Parses GAV string and returns dict with its components suitable for nexus calls
    """

    if isinstance (gav, dict):
        if any([relaxed, set(['a', 'g', 'v']).issubset(set(gav.keys()))]): return gav
        raise ValueError("Expected string or dict with g/a/v but got dict")

    if relaxed and (gav == None or gav == ''): return {}
    if not isinstance (gav, strtype): raise ValueError("Expected string but got " + str(type(gav)))
    gav_list = gav.split(':')
    if len(gav_list) < 3 and not relaxed: raise ValueError("GroupId, ArtifactId and Version are mandatory")
    if len(gav_list) > 5: raise ValueError("Incorrect GAV format")
    gav_dict = {}
    for i, v in enumerate(gav_list): gav_dict[['g', 'a', 'v', 'p', 'c'][i]] = v
    return gav_dict


def gav_to_path(gav, relaxed=False):
    """
    Converts GAV to repository path. Gav can be either string or dict from parse_gav function
    """

    if isinstance (gav, strtype):
        gav = parse_gav(gav, relaxed)

    if not relaxed and not set(['g', 'a', 'v']).issubset(set(gav.keys())):
        raise ValueError('ArtifactId, GroupId and Version are mandatory!')

    url = ''
    group_path = gav['g'].replace('.', posixpath.sep) if "g" in gav else ""
    artifact_path = gav_to_artifact_path(gav) if "a" in gav else ""
    url = posixpath.sep.join(filter(None, [group_path, artifact_path]))
    return url


def gav_to_artifact_path(gav):
    """ Converts gav to name like artifactid/version/filename """
    if isinstance (gav, strtype):
        gav = parse_gav(gav, relaxed=True)

    path = gav['a']

    if 'v' in gav:
        path = posixpath.join(path, gav['v'], gav_to_filename(gav))

    return path


def gav_to_filename(gav):
    """ Converts gav to name like artifactid-version.packaging """
    if isinstance (gav, strtype):
        gav = parse_gav(gav, relaxed=True)

    if not set(['a', 'v']).issubset(set(gav.keys())):
        raise ValueError("Artifactid and version required to make path")

    filename = '-'.join(
            filter(None, map(lambda x: gav.get(x), ['a', 'v', 'c'])))

    return '.'.join([filename, gav.get('p', 'jar')])

def gav_to_str(parsed_gav):
    """ Converts parsed GAV back to colon-separated string """
    required_keys=["g", "a", "v"]

    if not set(required_keys).issubset(set(parsed_gav.keys())):
        raise ValueError("At least groupid, artifactid and version should be presented in parsed gav")

    _result = ':'.join(map(lambda x: parsed_gav.get(x), required_keys))

    if not 'p' in parsed_gav.keys():
        return _result

    return ':'.join([_result] + list(filter(None, map(lambda x: parsed_gav.get(x), ['p', 'c']))))


def pom_from_gav(gav, no_packaging=True):
    """ 
    Generates pom file from gav
    """

    #  1. perhaps this is a good place to make it with:
    #       - pkg_resource - to get template itself 
    #       - jinja2.Template() - to fill it with values
    #     but it was not implemented to get rid of extra libraries dependency
    #  2. constructing it with xml.etree.ElementTree looks more correct
    #     but code will be longer than a template. 
    #       - ElementTree has many issues with constructing main <project> tag
    #       - Earlier versions of ElementTree are unable to write <?xml?> declaration to result output
    #       - Python2 and Python3 versions of ElementTree have different behaviour with return types of 'tostring'
    #           - For Python3 it is necessary to specify encoding='unicode', 
    #             otherwise result type will be 'bytes', not 'strtype'
    #           - Python2 version of ElementTree does not support 'unicode' encoding. 
    pom_template = '''<?xml version="1.0" encoding="UTF-8"?>
      <project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" 
            xmlns="http://maven.apache.org/POM/4.0.0" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <modelVersion>4.0.0</modelVersion>
        <groupId>{g}</groupId>
        <artifactId>{a}</artifactId>
        <version>{v}</version>
        {pkg}
      </project>
    '''

    if isinstance (gav, strtype):
        gav = parse_gav(gav)
    else:
        gav = gav.copy()

    if no_packaging or 'p' not in gav.keys():
        gav['pkg'] = ''
    else:
        gav['pkg'] = '<packaging>' + gav['p'] + '</packaging>'

    return pom_template.format(**gav)

def gav_from_path(path, dictionary=True):
    """
    Generate GAV from path to artifact.
    Path should be relative to main entrypoint
    And not should not contain repositoryId. Example:
    """
    generated_gav = {}
    path = path.strip('.').strip(posixpath.sep)
    path_parts = path.split(posixpath.sep)
    generated_gav['g'] = '.'.join(path_parts[:-3])
    generated_gav['a'] = path_parts[-3]
    generated_gav['v'] = path_parts[-2]

    file_name = posixpath.basename(path)
    _av_part = '{a}-{v}'.format(**generated_gav)
    _cp_part = None

    # Actually if filename does not start with '_av_part' in MVN - 
    # it is surely a bug, but we shall try to act gracefully
    if not file_name.startswith(_av_part):
        return generated_gav if dictionary else gav_to_str(generated_gav)

    _cp_part = file_name.replace(_av_part, '', 1).strip('-').strip('.')

    if not _cp_part:
        # nothing to parse for packaging and classifier
        return generated_gav if dictionary else gav_to_str(generated_gav)
        
    classifier, file_ext = posixpath.splitext(_cp_part)

    if file_ext:
        # So we have packaging info and classifier
        generated_gav['p'] = file_ext.strip('.')
        generated_gav['c'] = classifier
    else:
        # otherwise classifier is absent, so there is packaging there
        generated_gav['p'] = classifier

    return generated_gav if dictionary else gav_to_str(generated_gav)

class NexusAPI(HttpAPI):
    _error = NexusAPIError
    _env_prefix = 'MVN'
    _env_upload_repo = '_UPLOAD_REPO'
    _env_download_repo = '_DOWNLOAD_REPO'

    codepage = 'utf-8'
    codepage_errors = 'replace'

    def __init__(self, root=None, user=None, auth=None,
                 readonly=False, anonymous=False, upload_repo=None, download_repo=None):
        """
        :param root: service URL
        :type root: str
        :param user: username
        :type user: str
        :param auth: password or authentication token
        :type auth: str
        :param readonly: do not try to put anything to the server
        :type readonly: bool
        :param anonymous: forse anonymous connection, even if _USER and _PASSWORD are specified in
        :param anonymous: the environment
        :type anonymous: bool
        :param upload_repo: repository to upload artifacts to
        :type repo: str
        :param download_repo: repository to download artifacts from
        :type download_repo: str
        """
        super(NexusAPI, self).__init__(root, user, auth, readonly, anonymous)
        self.__upload_repo = upload_repo
        self.__download_repo = download_repo
    
    @property
    def repo_default(self):
        """
        Return default repo for different systems (former "public")
        """
        if self.is_artifactory: 
            return "maven-virtual"

        return "public"

    @property
    def is_artifactory(self):
        """
        Test if we are working with Artifactory, not with Nexus
        """
        return self.root.rstrip(posixpath.sep).endswith(posixpath.sep + "artifactory")

    @property
    def is_nexus(self):
        """
        Test if we are working with Nexus, not with Artifactory
        """
        return self.root.rstrip(posixpath.sep).endswith(posixpath.sep + "nexus")

    def gav_get_url(self, gav, repo=None):
        """
        Get full artifact URL.
        :param gav: gav
        :type gav: str, dict
        :param repo: repo
        :type repo: str
        """
        #urllib.urlparse.urljoin is not suitable for us since it joins only host part + relative part
        if not gav:
            raise ValueError("GAV is mandatory")

        return posixpath.join(self.root, self.__gav_get_url(gav, repo=repo))

    def __gav_get_url(self, gav, repo, relaxed=False):
        """
        Full sub-path for get/post requests to 'gav'
        :param gav: gav
        :type gav: str, dict
        :param repo: repo
        :type repo: str
        """
        _rq = posixpath.join(
                repo if repo else self.repo_default, 
                gav_to_path(gav, relaxed=relaxed) if gav else "")

        if self.is_nexus: 
            _rq = posixpath.join("content", "repositories", _rq)

        return _rq.rstrip(posixpath.sep)

    def cat(self, gav, repo=None, binary=False, response=False, stream=False, encoding=None, enc_errors=None,
            write_to=None, rest_call=False, **argv):
        """
        Gets data from maven repo
        :param gav: GAV
        :type gav: str
        :param repo: repository to search artifact in
        :type repo: str
        :param binary: return binary artifact data, without decoding to text
        :type binary: bool
        :param response: return HTTP response itself instead of artifact data
        :type response: bool
        :param stream: open file stream to further process artifact data, useful for large files
        :type stream: boolean
        :param enc_errors: behaviour on text decoding/encoding errors while processing artifact data
        :type enc_errors: str
        :param write_to: path or file_object to write artifact data to instead of returning it as result
        :type write_to: str, file_obj, ...
        :param rest_call: try to search artifact via REST API instead of getting directly from repository
        :param rest_call: WARNING: this flag is ignored for Artifactory
        :type rest_call: bool
        """

        # we set binary to true to ignore codepage issues
        params = parse_gav(gav)
        if not repo: repo = self.__download_repo
        if not repo: repo = os.getenv(self._env_prefix + self._env_download_repo, self.repo_default)
        params['r'] = repo

        # workaround Nexus REST API can't work with plain text files, so we use direct download instead
        if rest_call and self.is_nexus:
            r = self.get(posixpath.join('service', 'local', 'artifact', 'maven', 'content'), params, stream=stream, write_to=write_to, **argv)
        else:
            _rq = self.__gav_get_url(gav, repo=params['r'])
            r = self.get(_rq, stream=stream, write_to=write_to, **argv)

        if response or write_to: return r
        if binary: return r.content

        if not encoding: encoding = self.codepage
        if not enc_errors: enc_errors = self.codepage_errors
        if not enc_errors: enc_errors = 'strict'
        if encoding: return r.content.decode(encoding, enc_errors)

        return r.text

    def exists(self, gav, repo=None, rest_call=False):
        """
        Checks if artifact exists in repo
        :param gav: gav
        :type gav: str
        :param repo: repository to search artifact in:
        :type repo: str
        :param rest_call: search with REST API instead of direct path
        :param rest_call: WARNING: this flag is for Nexus only
        :type rest_call: bool
        """
        params = parse_gav(gav)

        if not repo: repo = self.__download_repo
        if not repo: repo = os.getenv(self._env_prefix + self._env_download_repo, self.repo_default)
        params['r'] = repo

        if rest_call and self.is_nexus:
            try:
                r = self.get(posixpath.join('service', 'local', 'artifact', 'maven', 'redirect'), params, allow_redirects=False)
            except NexusAPIError as e:
                if e.code == 404: return False
                raise (e)
            if r.status_code == 307: return True
            raise self._error(r.status_code, r.url, r, 'Incorrect response code - only 404 and 307 are expected')
        
        _req = self.__gav_get_url(gav, repo=params['r'])
        try:
            r = self.head(_req)
        except NexusAPIError as e:
            if e.code == 404: return False
            raise (e)
        if r.status_code == 200: return True

        raise self._error(r.status_code, r.url, r, 'Incorrect response code - only 404 and 200 are expected')

    def upload(self, gav, repo=None, data=None, pom=None, metadata=False):
        """ Puts data into maven repo under gav
        pom can be set to actual pom content or to True for automatic pom generation
        :param gav: GAV
        :type gav: str
        :param repo: repository to upload to
        :type repo: str
        :param data: data ot upload
        :type data: str, bytes, file-like object, ...
        :param pom: upload POM. POM data may be provided as value. If 'True' provided - upload auto-generated POM
        :type pom: str, bool
        :param metadata: update metadata
        :param metadata: WARNING: this flag is valid for Nexus only and ignored for others
        :type metadata: bool
        """
        if not repo: repo = self.__upload_repo
        if not repo: repo = os.getenv(self._env_prefix + self._env_upload_repo)
        if not repo: raise (ValueError("You must provide repo name"))

        # Raise exception manually instead of
        # making data mandatory for backwards-compatibility
        if data == None: raise (ValueError("No data to upload"))

        # Requests uses 'multipart/form-data' header by default, which is not supported by Artifactory.
        custom_headers = {'Content-Type': 'application/binary'}

        # TODO: temporal hack, to be removed
        #       'repo' may be "repositories/id/sub" or longer. This case we need second component only.
        if repo.startswith('repositories' + posixpath.sep): repo = repo.split(posixpath.sep)[1]

        url = self.__gav_get_url(gav, repo=repo)
        params = parse_gav(gav)
        params['p'] = 'pom'
        pom_url = self.__gav_get_url(params, repo=repo)

        # we need 'True' exactly
        if pom is True: 
            # don't try to upload auto-generated pom if there is existing one
            if self.exists(params, repo=repo): pom = False
            else: pom = pom_from_gav(gav, no_packaging=True)

        # uploading generated or provided pom
        if pom: self.put(pom_url, data=pom, headers=custom_headers)
        resp = self.put(url, data=data, headers=custom_headers)

        if all([self.is_nexus, pom, metadata]): self.update_metadata(params['g'], repo)

        return resp

    def update_metadata(self, gav=None, repo=None):
        """
        Update metadata in repo for gav
        :param gav: GAV
        :type gav: str
        :param repo: repository ID
        :type repo: str
        """
        if not self.is_nexus:
            return None

        if not repo: repo = self.__upload_repo
        if not repo: repo = os.getenv(self._env_prefix + self._env_upload_repo)
        if not repo: raise (ValueError("You must provide repo name"))

        _req = posixpath.join("service", "local", "metadata", "repositories", repo, 'content')
        
        if gav:
            _req = posixpath.join(_req, gav_to_path(gav, relaxed=True))

        return self.delete(_req)

    def __check_filter(self, str_artifact, str_filter, b_filter_revert):
        if not str_filter:
            return True

        re_filter = re.compile(r'' + str_filter)

        if (not b_filter_revert) and (re_filter.search(str_artifact) is not None):
            return True

        if (b_filter_revert) and (re_filter.search(str_artifact) is None):
            return True

        return False

    #TODO: replace 'filter' keyword argument - it is RESERVED in recent Python interpreters
    def ls(self, gav, repo=None, filter=None, filter_revert=False):
        """
        List of artifacts suitable for filter in repository given
        :param gav: gav to search for, may be regular expression
        :tytpe gav: str
        :param repo: repository ID
        :type repo: str
        :param filter: filter for artifacts
        :type filter: dict
        """
        if self.is_nexus: return self.__ls_nexus(gav, repo=repo, filter=filter, filter_revert=filter_revert)
        if self.is_artifactory: return self.__ls_artifactory(gav, repo=repo, filter=filter, filter_revert=filter_revert)
        raise NotImplementedError("Not implemented for '%s'" % posixpath.basename(self.root.rstrip(posixpath.sep)))

    # the same for specific systems
    def __ls_artifactory(self, gav, repo=None, filter=None, filter_revert=False):
        parsed_gav = parse_gav(gav, relaxed=True)
        search_parameters = parsed_gav.copy()

        # Artifactory does not provide search by packaging
        # so we have to filter it manually
        if "p" in search_parameters:
            del(search_parameters["p"])

        if repo:
            search_parameters['repos'] = repo

        artifacts = []

        _req = posixpath.join("api", "search", "gavc")

        # we need to return empty list if we found nothing
        try:
            resp = self.get(_req, params=search_parameters, headers={'X-Result-Detail': 'info'})
            resp = resp.json()
            resp = resp.get('results')
        except NexusAPIError as e:
            if e.code != 404:
                logging.exception(e)

            return artifacts

        if not resp:
            return artifacts


        for artifact in resp:
            # no path - no artifact

            if not artifact.get("path"):
                continue

            artifact_gav_dict = gav_from_path(artifact.get('path'))

            # historically we are not interested in POMs
            if artifact_gav_dict.get('p') == "pom":
                continue

            # if we are asked to search for exact packaging - filter it
            if all(["p" in parsed_gav, parsed_gav.get("p") != artifact_gav_dict.get("p")]):
                continue

            # check our artifact for filter
            generated_gav = gav_from_path(artifact.get('path'), dictionary=False)
            
            if self.__check_filter(generated_gav, filter, filter_revert):
                artifacts.append(generated_gav)

        return list(set(artifacts))

    def __ls_nexus(self, gav, repo=None, filter=None, filter_revert=False):
        g_s = parse_gav(gav, relaxed=True)
        g_p = dict()
        ls_artif = None

        if not g_s.get('a'):
            ls_artif = list()

        # Filter values of parsed GAV for Lucene Search search Nexus plugin
        # Packaging is to be excluded due to that plugin "feature"
        for ch_key in ['g', 'a', 'v', 'c']:
            if g_s.get(ch_key):
                g_p[ch_key] = g_s[ch_key]

        if repo:
            g_p['repositoryId'] = repo

        resp = self.get(posixpath.join("service", "local", "lucene", "search"), g_p)
        xml = ElementTree.fromstring(resp.content)
        artifacts = []
        for artifact in xml.find('data').findall('artifact'):
            for hit in artifact.find('artifactHits').findall('artifactHit'):
                b_ext_found = False
                if not 'p' in g_s:
                    b_ext_found = True; # do not search if we was not asked for it

                for ext_t in hit.find('artifactLinks').findall('artifactLink'):
                    ext = ext_t.find('extension')

                    if (ext is not None and ext.text == 'pom'):
                        continue

                    clsf = ext_t.find('classifier')
                    str_artifact_full = gav_to_str({
                        'g': artifact.find('groupId').text,
                        'a': artifact.find('artifactId').text,
                        'v': artifact.find('version').text,
                        'p': ext.text if ext is not None else None,
                        'c': clsf.text if clsf is not None else None})

                    __unused, str_artifact = str_artifact_full.split(':', 1)
                    
                    if not self.__check_filter(str_artifact, filter, filter_revert):
                        continue

                    if not g_s.get('p'):
                        if str_artifact_full not in artifacts \
                                and self.exists(str_artifact_full, repo=repo):
                            artifacts.append(str_artifact_full)

                        continue

                    if ext is not None and g_s.get('p') != ext.text:
                        continue

                    b_ext_found = bool(ext is not None and ext.text)

                    if str_artifact_full not in artifacts:
                        artifacts.append(str_artifact_full)

                if not b_ext_found:
                    # produce fake gav and check if exist
                    str_artifact_full = gav_to_str({
                        'g': artifact.find('groupId').text,
                        'a': artifact.find('artifactId').text,
                        'v': artifact.find('version').text,
                        'p': g_s.get('p'),
                        'c': g_s.get('c')})

                    if str_artifact_full in artifacts:
                        continue

                    __unused, str_artifact = str_artifact_full.split(':', 1)

                    if not self.__check_filter(str_artifact, filter, filter_revert):
                        continue

                    if self.exists(str_artifact_full):
                        artifacts.append(str_artifact_full)

            if ls_artif is not None and artifact.find('artifactId').text not in ls_artif:
                ls_artif.append(artifact.find('artifactId').text)

        if ls_artif is not None:
            for str_art in ls_artif:
                # here we may not use gav_to_str since
                # we need empty values for some attributes, 
                # but gav_to_str silently skips them
                # or raises undesirable exception
                str_gav_c = ':'.join([
                    g_s.get('g'), 
                    str_art,
                    g_s.get('v', ""),
                    g_s.get('p', ""),
                    g_s.get('c', "")])

                artifacts += self.__ls_nexus(str_gav_c, repo, filter, filter_revert)

        return list(set(artifacts))

    def info(self, gav, repo=None):
        """
        Get md5 checksum for a gav from file
        :param gav:  string, g:a:v:p
        :type gav: str
        :param repo: string, repository_id
        :type repo: str
        :return: artifact information: md5sum, mime-type
        :return type: dict, None
        """
        if not repo: repo = self.repo_default

        if self.is_nexus: return self.__info_nexus(gav, repo=repo)
        if self.is_artifactory: return self.__info_artifactory(gav, repo=repo)
        raise NotImplementedError("Not implemented for '%s'" % posixpath.basename(self.root.rstrip(posixpath.sep)))

    ### the same as general info for different systems
    def __info_artifactory(self, gav, repo):
        _req = posixpath.join("api", "storage", repo, gav_to_path(gav))

        try:
            http_resp = self.get(_req)
        except NexusAPIError as e:
            # Artifactory returns 404 if file is not found
            # or information about it is not (yet?) available
            if e.code != 404: 
                logging.exception(e)

            return None

        if not http_resp or not http_resp.content:
            return None

        response_json = http_resp.json()

        if response_json is None:
            return None

        # NOTE about 'dict()' default value for first 'get'
        # we do not want to raise an exception "NoneType object has no 'get' attribute"
        artifact_md5 = response_json.get('checksums', dict()).get('md5')
        artifact_mime = response_json.get('mimeType')

        if any([not artifact_md5, not artifact_mime]):
            return None

        return {"md5": artifact_md5, "mime": artifact_mime}

    def __info_nexus(self, gav, repo):
        str_path = posixpath.join("service", "local", "repositories", repo, "content", gav_to_path(gav))
        dict_parms = {"describe" : "info"}
        http_resp = self.get(str_path, dict_parms)

        if not http_resp or not http_resp.content:
            return None

        obj_xml = ElementTree.fromstring(http_resp.content)

        # NOTE: xml.etree.ElementTree drops warning if simple 'not obj_xml' is used
        #       explicitly comparison is strictly recommended
        if (obj_xml is None):
            return None

        xml_tag_md5 = obj_xml.find("./data/md5Hash")
        xml_tag_mime = obj_xml.find("./data/mimeType")

        if any([xml_tag_md5 is None, xml_tag_mime is None]):
            return None

        return {"md5" : xml_tag_md5.text, "mime" : xml_tag_mime.text}


    def remove(self, gav=None, repo=None):
        """
        Remove artifact by gav
        :param gav: string, artifact gav to remove
        :param repo: string, repository containing artifact
        :return: Response, response for delete request
        """

        if not repo:
            repo = self.__upload_repo
        if not repo:
            repo = os.getenv(self._env_prefix + self._env_upload_repo)
        if not repo:
            raise (ValueError("You must provide repo name"))

        _req = self.__gav_get_url(gav, repo=repo, relaxed=True)

        return self.delete(_req)

