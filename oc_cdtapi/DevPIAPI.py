#!/usr/bin/python2.7

"""
Additional HTTP API for Python Package Index based on DevPI
"""

from .API import HttpAPI;
import re;
import xml.etree.ElementTree as ET;
import posixpath;

class DevPIAPI( HttpAPI ):
    """
    Class for providing some simple Http requests to PyPI based on DevPI 
    """
    _env_prefix = "PYPI_PRODUCTION";

    def _split_pkg_string( r_self, str_name ):
        """
        Split string for package name into components following PyPI standard
        :param r_self: self reference
        :type r_self: DevPIApi object
        :param str_name: python package name
        :type str_name: string, unicode
        :return: dictionary with components: distribution, version, build_tag, python_tag, abi_tag, platform_tag. Some of them may be absent
        """

        obj_match = re.match( r'^(?P<distribution>[^\.]*)-(?P<version>[\d\.]+)(-(?P<build_tag>[^\-]+))?-(?P<python_tag>[^\-]+)-(?P<abi_tag>[^\-]+)-(?P<platform_tag>[^\-\.]+)\.whl$', str_name );

        if obj_match is None:
            obj_match = re.match( r'^(?P<distribution>[^\.]*)-(?P<version>[\d\.]+)\.tar\.gz$', str_name );

        if obj_match is None:
            raise ValueError( 'DevPI answer is wrong: package name ' + str_name + " does not match any known pattern" );

        return obj_match.groupdict();

    def get_package_versions( r_self, str_name ):
        """
        Get package version list from server
        :param r_self: self reference
        :type r_self: DevPIApi object
        :param str_name: python package name
        :type str_name: string, unicode
        :return: list of versions on the server, or None if nothing found
        """

        str_name = str_name.strip();
        str_request = posixpath.join( "+simple", str_name );
        obj_resp = r_self.get( str_request );

        if ( obj_resp.status_code != 200 ):
            return None;

        xml_resp = ET.fromstring( obj_resp.text );

        return list( set( [r_self._split_pkg_string( x.text )[ 'version' ] for x in xml_resp.findall( 'body/a' )] ) )
