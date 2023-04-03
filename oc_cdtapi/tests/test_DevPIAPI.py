import unittest
from oc_cdtapi.DevPIAPI import DevPIAPI;
import os;
import posixpath;
import xml.etree.ElementTree as ET;
import random;

## fake URL
str_fake_devpi_url = posixpath.join( "http:" + posixpath.sep + posixpath.sep, "fake.devpi.url", "fakerepo" );

## fake packages list
dict_fake_packages = {
        "blob-the-dog" : [ "1.0.0.24", "1.1.0.333", "1.1.1.1111" ],
        "get-out-of-here": [ "1.4.6.33451254", "1.4.7.44731" ]
        }

class _Response( object ):
    """
    Fake HTTP response
    """

    text = None;
    status_code = None;

class _DevPIAPI( DevPIAPI ):
    def _random_pkg_file( r_self, str_pkg, str_vers ):
        """
        generate random package file name
        """
        if ( random.randint( 0, 1 ) == 0 ):
            return "-".join( [ str_pkg, str_vers, "py2", "none", "any.whl" ] );

        return "-".join( [ str_pkg, str_vers + ".tar.gz" ] );


    def get( r_self, req, params = None, files = None, data = None, headers = None, **kvarg ):
        """
        Here we shall construct a fake HTML response
        """

        req = req.replace( str_fake_devpi_url, "" ).replace( "+simple", "" ).strip().strip( posixpath.sep );
        # here we should have a component only

        resp = _Response();
        resp.url = posixpath.join( str_fake_devpi_url, req );

        if req not in dict_fake_packages:
            resp.status_code = 404; # NOT FOUND
            resp.text = None;
            return resp;

        resp.status_code = 200; #OK

        xml_resp_root = ET.Element( "html" );
        xml_resp_body = ET.Element( "body" );
        xml_resp_root.append( xml_resp_body );

        for str_vers in dict_fake_packages[ req ]:
            xml_a_tag = ET.Element( "a" );
            str_full_pkg_file = r_self._random_pkg_file ( req, str_vers );
            xml_a_tag.attrib[ 'href' ] = posixpath.join( "..", "..", "+f", "00", "00", str_full_pkg_file );
            xml_a_tag.text = str_full_pkg_file;
            xml_resp_body.append( xml_a_tag );

        resp.text = ET.tostring( xml_resp_root );

        return resp;

class TestDevPIAPI( unittest.TestCase ):
    def test_get_versions( r_self ):
        os.environ[ "PYPI_PRODUCTION_URL" ] = str_fake_devpi_url;
        obj_api = _DevPIAPI();

        for str_pkg in dict_fake_packages.keys():
            test_result = True
            eth_arr = dict_fake_packages [str_pkg]
            cmp_arr = obj_api.get_package_versions (str_pkg)
            for eth_val in eth_arr:
                if not eth_val in cmp_arr:
                    test_result = False
            r_self.assertTrue (test_result)
#            r_self.assertEqual( dict_fake_packages[ str_pkg ], obj_api.get_package_versions( str_pkg ) );

        r_self.assertIsNone( obj_api.get_package_versions( "this_package-does_not-exist" ) );
