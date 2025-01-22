#!/usr/bin/python2.7

"""
Additional HTTP API for Python Package Index based on DevPI
"""

from .API import HttpAPI
import re
import xml.etree.ElementTree as ET
import posixpath


class DevPIAPI(HttpAPI):
    """
    Class for providing some simple Http requests to PyPI based on DevPI 
    """
    _env_prefix = "PYPI_PRODUCTION"

    def _split_pkg_string(self, name):
        """
        Split string for package name into components following PyPI standard
        :param str name: python package name
        :return dict: components: distribution, version, build_tag, python_tag, abi_tag, platform_tag.
                      Some of them may be absent
        """

        _match = re.match(
            r'^(?P<distribution>[^\.]*)-(?P<version>[\d\.]+)(-(?P<build_tag>[^\-]+))?-(?P<python_tag>[^\-]+)-(?P<abi_tag>[^\-]+)-(?P<platform_tag>[^\-\.]+)\.whl$', name)

        if _match is None:
            _match = re.match(r'^(?P<distribution>[^\.]*)-(?P<version>[\d\.]+)\.tar\.gz$', name)

        if _match is None:
            raise ValueError('DevPI answer is wrong: package name [%s] does not match any known pattern' % name)

        return _match.groupdict()

    def get_package_versions(self, name):
        """
        Get package version list from server
        :param self: self reference
        :type self: DevPIApi object
        :param name: python package name
        :type name: string, unicode
        :return: list of versions on the server, or None if nothing found
        """

        name = name.strip()
        _request = posixpath.join("simple", name)
        _resp = self.get(_request)

        if (_resp.status_code != 200):
            return None

        xml_resp = ET.fromstring(_resp.text)

        return list(set([self._split_pkg_string(x.text)['version'] for x in xml_resp.findall('body/a')]))
