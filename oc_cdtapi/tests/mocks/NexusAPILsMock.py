from oc_cdtapi import NexusAPI
import posixpath
from copy import deepcopy
from xml.etree import ElementTree
import re
import json

class ResponseMock(object):
    def __init__(self, url, status_code, content = None):
        self.status_code = status_code
        self.content = content
        self.url = url

    def json(self):

        if not self.content:
            return None

        return json.loads(self.content)

class NexusAPILsMock(object):
    """
    Helper class for Nexus API responses on test LS capabilities
    """
    def __init__(self, url=None):
        # list of artifacts to provide
        # four groups are enough
        self._url = url
        self.packaging = ["jar", "zip", "tgz", "rpm"]
        self.classifiers = ["cl", "vx"]
        self.groups = len(self.packaging)
        self.artifacts = len(self.packaging)
        self.versions = len(self.packaging)
        self.__artifacts = list()

        # generating some test artifacts
        for __group in list(map(lambda x: "test.group.%d.id" % x, range(0, self.groups))):
            for __artifact in list(
                    map(lambda x: ":".join([__group, "artifact-%d" % x]), range(0, self.artifacts))):
                for __version in list(
                        map(lambda x: ":".join([__artifact, "%d.%d.%d" % (x, x+x, x*x)]), range(0, self.versions))):
                    for __packaging in list(
                            map(lambda x: ":".join([__version, self.packaging[x]]), range(0, len(self.packaging)))):
                        for __classifier in range(0, len(self.classifiers) + 1):
                            if __classifier >= len(self.classifiers):
                                self.__artifacts.append(NexusAPI.parse_gav(__packaging))
                                continue

                            self.__artifacts.append(NexusAPI.parse_gav(
                                ":".join([__packaging, self.classifiers[__classifier]])))

    @property
    def __is_nexus(self):
        return self._url.rstrip(posixpath.sep).endswith(posixpath.sep + "nexus")

    def _strip_request_url(self, url):
        if not url.startswith(self._url):
            raise ValueError("Incorrect request URL")

        # NOTE: this should be done by urllib.urlparse,
        #       but done so ugly to get rid of extra dependencies
        url = url[len(self._url):].strip(posixpath.sep)
        return url

    def _filter_artifacts(self, params):

        _res = deepcopy(self.__artifacts)

        for __p in ['g', 'a', 'v', 'p', 'c']:
            if not params.get(__p):
                continue

            _res = list(filter(lambda x: x.get(__p) == params.get(__p), _res))

        return _res

    def __xml_search_response(self, lst, too_many_results):
        _rsp = ElementTree.Element("searchNGResponse")
        _tc = ElementTree.SubElement(_rsp, "totalCount")
        _tc.text = str(len(lst))
        _tmr = ElementTree.SubElement(_rsp, "tooManyResults")
        _tmr.text = str(too_many_results).lower()
        _data = ElementTree.SubElement(_rsp, "data")

        if not len(lst):
            return _rsp

        _gav = list()

        for _af in lst:
            _dct = dict()

            for _k in ["g", "a", "v"]:
                _dct[_k] = _af.get(_k)

            _gav_s = NexusAPI.gav_to_str(_dct)

            if _gav_s in _gav:
                continue

            _gav.append(_gav_s)

            _afx = ElementTree.SubElement(_data, "artifact")
            ElementTree.SubElement(_afx, "groupId").text = _af.get("g")
            ElementTree.SubElement(_afx, "artifactId").text = _af.get("a")
            ElementTree.SubElement(_afx, "version").text = _af.get("v")

            # add "pom" packaging
            _af_hits = ElementTree.SubElement(_afx, "artifactHits")
            _af_hit = ElementTree.SubElement(_af_hits, "artifactHit")


            _af_links = ElementTree.SubElement(_af_hit, "artifactLinks")

            for _pkg in ["pom", _af.get("p")]:
                _af_link = ElementTree.SubElement(_af_links, "artifactLink")

                ElementTree.SubElement(_af_link, "extension").text = _pkg

                if _pkg == "pom" or not _af.get("c"):
                    continue

                ElementTree.SubElement(_af_link, "classifier").text = _af.get("c")

            if too_many_results: 
                continue

            for _afs in list(filter(lambda x: 
                all(list(map(lambda y: x.get(y)==_af.get(y), ["g", "a", "v"]))), lst)):

                if all(list(map(lambda x: _afs.get(x) == _af.get(x), ["p", "c"]))):
                    continue

                _af_link = ElementTree.SubElement(_af_links, "artifactLink")
                ElementTree.SubElement(_af_link, "extension").text = _afs.get("p")

                if not _afs.get("c"):
                    continue

                ElementTree.SubElement(_af_link, "classifier").text = _afs.get("c")

        return _rsp

    def get(self, req, params=None, data=None, files=None, headers=None, **kvargs):
        __req = self._strip_request_url(req)

        if __req != posixpath.join("service", "local", "lucene", "search"):
            raise ValueError("Unsupported request: %s" % req)

        if not params:
            raise ValueError("Search parameters shoud not be empty")

        _pres = self._filter_artifacts(params)

        return ResponseMock(req, 200, 
                content=ElementTree.tostring(
                    self.__xml_search_response(_pres, too_many_results=("a" not in params.keys()))))

    def head(self, req, params=None, data=None, files=None, headers=None, **kvargs):
        __req = self._strip_request_url(req)
        _apath = __req

        if self.__is_nexus:
            if not __req.startswith(posixpath.join('content', 'repositories')):
                raise ValueError("Unsupported request: %s" % req)

            _apath = posixpath.sep.join(__req.split(posixpath.sep)[len(["content", "repositories", "public"]):])

        __gav = NexusAPI.gav_from_path(_apath, dictionary=True)

        return ResponseMock(req, 200 if __gav in self.__artifacts else 404)


class ArtifactoryAPILsMock(NexusAPILsMock):
    def __json_search_response(self, lst):
        _res = list()

        for _a in lst:
            _pth = NexusAPI.gav_to_path(_a)
            _res.append({
                "uri": posixpath.join(self._url, "api", "storage", "public", _pth),
                "path": posixpath.sep + _pth })

        return {"results":_res}

    def get(self, req, params=None, data=None, files=None, headers=None, **kvargs):
        __req = self._strip_request_url(req)

        if __req != posixpath.join("api", "search", "gavc"):
            raise ValueError("Unsupported request: %s" % req)

        if not params:
            raise ValueError("Search parameters shoud not be empty")

        if 'p' in params:
            raise ValueError("Packaging search is not supported by Artifactory")

        if not headers or "X-Result-Detail" not in headers:
            raise ValueError("Suppose header 'X-Result-Detail' for Artifactory search")

        _pres = self._filter_artifacts(params)

        return ResponseMock(req, 200, content=json.dumps(self.__json_search_response(_pres)))
