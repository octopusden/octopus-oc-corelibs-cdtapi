import unittest
from oc_cdtapi.JenkinsAPI import Build, QueueItem, BuildStatus, BuildStatusException, JenkinsError, Jenkins
from requests import Response
from collections import namedtuple, OrderedDict
import re, posixpath;
import json;
import os;
import sys


MockResponse=namedtuple("MockResponse", ("status_code", "headers", "text", ))


class TestClient(object):

    def __init__(self, responses=[MockResponse(200, {}, ""), ]):
        self.responses=iter(responses)

    def get(self, relative_path, *args, **kwargs):
        return next(self.responses)

class TestJenkinsClient( Jenkins ):
    ls_jobs_disabled = list();
    dict_jobs_exist = dict();
    ## responses on slave-specific data
    computer_data = {
                'master': None,
                'test-node' : {"executors":[
                {"currentExecutable":{  "actions":[{},{},{},{},{},{}],
                                        "artifacts":[],
                                        "building":True,
                                        "description":None,
                                        "duration":0,
                                        "estimatedDuration":1706173,
                                        "executor":{},
                                        "fullDisplayName":"c.TEST_CUSTOMER.branches-test.test #27",
                                        "id":"2018-11-21_09-51-15",
                                        "keepLog":False,
                                        "number":27,
                                        "result":None,
                                        "timestamp":1542783075808,
                                        "url":"http://localhost:8080/job/c.TEST_CUSTOMER.branches-test.test/27/",
                                        "builtOn":"test-node",
                                        "changeSet":{},
                                        "culprits":[{}],
                                        "fingerprint":[]},
                "idle":False}]},
            'other-node': {"executors":[
                {"currentExecutable":{  "actions":[{},{},{},{},{},{}],
                                        "artifacts":[],
                                        "building":True,
                                        "description":None,
                                        "duration":0,
                                        "estimatedDuration":1706173,
                                        "executor":{},
                                        "fullDisplayName":"c.TEST_CUSTOMER.trunk.test #3",
                                        "id":"2018-11-21_09-51-15",
                                        "keepLog":False,
                                        "number":3,
                                        "result":None,
                                        "timestamp":154383075808,
                                        "url":"http://localhost:8080/job/c.TEST_CUSTOMER.trunk.test/3/",
                                        "builtOn":"other-node",
                                        "changeSet":{},
                                        "culprits":[{}],
                                        "fingerprint":[]},
                "idle":False}]}
            }

    queue_data = { "items":
                [   {"actions":[
                        {"causes":[{"shortDescription":"Started by an SCM change"},{"shortDescription":"Started by an SCM change"}]},
                        {"parameters":[{"name":"OWS_HOME","value":"/local/homes/ows_home"},{"name":"action","value":"reinstall"},{"name":"version","value":"default"}]}],
                    "blocked":True,
                    "buildable":False,
                    "id":9590,
                    "inQueueSince":1542791418408,
                    "params":"\nOWS_HOME=/local/homes/ows_home\naction=reinstall\nversion=default",
                    "stuck":False,
                    "task":{    "name":"c.OWI_LUXCTRL.branches-int.cards",
                                "url":"http://localhost:8080/job/c.OWI_LUXCTRL.branches-int.cards/",
                                "color":"red_anime" },
                    "url":"queue/item/9590/",
                    "why":"Build 9589 is in progress",
                    "buildableStartMilliseconds":1542791433530},
                    {"actions":[
                        {"parameters":[{"name":"REINSTALLORACLE","value":False},{"name":"DOCLEANUP","value":False}]},
                        {},
                        {"causes":[{"shortDescription":"Started by upstream project \"tech.selfcheck\" build number 38,163",
                            "upstreamBuild":38163,
                            "upstreamProject":"tech.selfcheck",
                            "upstreamUrl":"job/tech.selfcheck/"}]}],
                    "blocked":False,
                    "buildable":True,
                    "id":9559,
                    "inQueueSince":1542790144130,
                    "params":"\nREINSTALLORACLE=False\nDOCLEANUP=False",
                    "stuck":True,
                    "task":{    "name":"hosts=cislaveora-25",
                                "url":"http://localhost:8080/job/tech.selfcheck/hosts=cislaveora-25/","color":"blue"},
                    "url":"queue/item/9559/",
                    "why":"Waiting for next available executor on cislaveora-25",
                    "buildableStartMilliseconds":1542790144130,
                    "pending":False}] }

    def _computer_data_to_jobs_data( self ):
        dict_result = dict();
        dict_result[ "jobs" ] = list();
        
        for t in self.computer_data.keys():
            if self.computer_data[ t ] is None:
                continue;

            if "executors" not in self.computer_data[ t ]:
                continue;

            for executor in self.computer_data[ t ][ "executors" ]:

                if executor is None or "currentExecutable" not in executor:
                    continue;

                job_name = executor[ "currentExecutable" ][ "fullDisplayName" ].split( " " )[ 0 ];
                dict_job = { "name" : job_name, "lastBuild" : executor[ "currentExecutable" ] };
                dict_job[ "lastBuild" ][ "builtOn" ] = t;
                dict_result[ "jobs" ].append( dict_job );

        return dict_result;

    class GetResponse( object ):
        text = None;

    last_post_url = None;
    last_post_data = None;

    def post( self, str_url, **kwargs ):
        self.last_post_data = kwargs;
        self.last_post_url = str_url;
        return str_url, kwargs;

    def get( self, str_url, *args, **kwargs ):
        if str_url is None or len( str_url ) == 0:
            obj_resp = self.GetResponse();
            obj_resp.text = json.dumps( self._computer_data_to_jobs_data() );
            return obj_resp;

        if str_url.startswith( 'queue' ):
            str_rq = str_url.rstrip('queue').lstrip( posixpath.join( 'api','json' )).strip( posixpath.sep );

            if len( str_rq ) == 0:
                obj_resp = self.GetResponse();
                obj_resp.text = json.dumps( self.queue_data );
                return obj_resp;

            if str_rq.startswith( 'item' ):
                int_item_id = int( str_rq.rstrip( 'item' + posixpath.sep ).strip().strip( posixpath.sep ) );

                for dict_item in self.queue_data[ 'items' ]:
                    if not dict_item[ "id" ] == int_item_id:
                        continue;
                    
                    obj_resp = self.GetResponse();
                    obj_resp.text = json.dumps( dict_item );
                    return obj_resp;

                return self.GetResponse();

        if str_url.startswith( 'computer' ):
            if posixpath.sep not in str_url.strip().strip( posixpath.sep ):
                obj_resp = self.GetResponse();
                ls_resp = map ( lambda x: { "displayName" : x }, self.computer_data.keys() );
                str_json = { "computer" : list (ls_resp) }
                obj_resp.text = json.dumps( str_json );
#                obj_resp.text = json.dumps( { "computer" : ls_resp } );
                return obj_resp;

            ls_comps = str_url.split( posixpath.sep );
            str_comp_name = ls_comps[1];

            if len( ls_comps ) < 3:
                obj_resp = self.GetResponse();
                obj_resp.text = json.dumps( self.computer_data[ str_comp_name ] );
                return obj_resp;

            str_action = ls_comps[2];

            if str_action == "config.xml":
                obj_resp = self.GetResponse();
                obj_resp.text = "<node><name>" + str_comp_name + "</name><label>" + str_comp_name + "</label></node>";
                return obj_resp;

            raise ValueError( 'Node (computer) action "' + str_action + "' is not supported" );

        if str_url.startswith( 'job' + posixpath.sep ):
            ls_jobs = str_url.split( posixpath.sep );
            str_job_name = ls_jobs[1];
            str_job_action = ls_jobs[2];

            if str_job_action == "config.xml" :
                if not str_job_name in self.dict_jobs_exist:
                    jerr = JenkinsError( str_job_name + " not found" );
                    jerr.code = 404;
                    raise jerr;

                obj_rsp = self.GetResponse();
                obj_rsp.text = self.dict_jobs_exist[ str_job_name ];

                if obj_rsp.text is None:
                    obj_rsp.text = "<job><name>" + str_job_name + "</name><disabled>" + ( "true" if ( str_job_name in self.ls_jobs_disabled ) else "false" ) + "</disabled><posBuild><action><disabled>true</disabled></action></postBuild></job>";

                return obj_rsp;

            raise ValueError( 'Job action "' + str_action + '" is not supported' );

        raise ValueError( "URL '" + str_url + "' is not supported." );
    
class QueueItemTestSuite(unittest.TestCase):
    
    def test_initial_state(self):
        mock_response="""
        {
            "task": {
                "name": "job"
            }
        }
        """
        item=QueueItem(1, TestClient([MockResponse(200, {}, mock_response),
                                      MockResponse(200, {}, mock_response),]))
        self.assertFalse(item.is_running())
        self.assertEqual(1, item.queue_id)
        with self.assertRaises(BuildStatusException):
            _=item.get_build()

    def test_invalid_queue_id(self):
        item=QueueItem(1, TestClient([MockResponse(404, {}, "{}")]))
        with self.assertRaises(JenkinsError):
            item.is_running()

    def test_build_still_queued(self):
        mock_response="""
        {
            "task": {
                "name": "job"
            }
        }
        """
        item=QueueItem(1, TestClient([MockResponse(200, {}, mock_response),
                                      MockResponse(200, {}, mock_response),]))
        self.assertFalse(item.is_running())
        with self.assertRaises(BuildStatusException):
            _=item.get_build()
            
    def test_build_started(self):
        mock_response="""
        {
            "task": {
                "name": "job"
            }, 
            "executable": {
                "number": 42
            }
        }
        """
        item=QueueItem(1, TestClient([MockResponse(200, {}, mock_response),
                                      MockResponse(200, {}, mock_response),]))
        self.assertTrue(item.is_running())
        build=item.get_build()
        self.assertEqual("job", build.job_name)
        self.assertEqual(42, build.build_number)

    def test_queue_status_updated(self):
        mock_response_1="""
        {
            "task": {
                "name": "job"
            }
        }
        """
        mock_response_2="""
        {
            "task": {
                "name": "job"
            }, 
            "executable": {
                "number": 42
            }
        }
        """
        item=QueueItem(1, TestClient([MockResponse(200, {}, mock_response_1),
                                      MockResponse(200, {}, mock_response_2),]))
        self.assertFalse(item.is_running())
        self.assertTrue(item.is_running())

    def test_jenkins_response_parsed(self):
        response=MockResponse(200, {"Location": "http://ci.com:123/queue/item/42/"}, [])
        item=QueueItem.from_jenkins_response(response, TestClient())
        self.assertEqual(42, item.queue_id)


class BuildTestSuite(unittest.TestCase):

    def test_running_build_status(self):
        mock_response="""
        {"result": null}
        """
        build=Build("job", 42, TestClient([MockResponse(200, {}, mock_response, )]))
        self.assertEqual("job", build.job_name)
        self.assertEqual(42, build.build_number)
        self.assertEqual(BuildStatus.BUILDING, build.get_status())

    def test_finished_build_status(self):
        mock_response="""
        {"result": "FAILURE"}
        """
        build=Build("job", 42, TestClient([MockResponse(200, {}, mock_response, )]))
        self.assertEqual("job", build.job_name)
        self.assertEqual(42, build.build_number)
        self.assertEqual(BuildStatus.FAILURE, build.get_status())

    def test_build_status_updated(self):
        mock_response_1="""
        {"result": null}
        """
        mock_response_2="""
        {"result": "SUCCESS"}
        """
        build=Build("job", 42, TestClient([MockResponse(200, {}, mock_response_1),
                                           MockResponse(200, {}, mock_response_2)]))
        self.assertEqual(BuildStatus.BUILDING, build.get_status())
        self.assertEqual(BuildStatus.SUCCESS, build.get_status())

    def test_invalid_build_params(self):
        build=Build("job", 42, TestClient([MockResponse(404, {}, "{}")]))
        with self.assertRaises(JenkinsError):
            build.get_status()

def xml_norm( str_xml ):
    parm_type = str (type (str_xml) )
    str_cmp = str_xml

    if parm_type != "<class 'str'>" and sys.version_info.major == 3:
        str_cmp = str (str_xml, 'UTF-8')

    str_cmp = re.sub( r'<\?xml[^<>]*>', '', str_cmp );
    str_cmp = re.sub( r'[\n\r]*', '', str_cmp );

    return str_cmp


class XMLTestSuite( unittest.TestCase ):
    def setUp( r_self ):
        os.environ[ 'JENKINS_URL' ] = 'http://localhost:8080';

    def test_get_node_label_from_config( self ):
        jnk = Jenkins();
        self.assertEqual( jnk.get_node_label_from_config( "<node><label>test</label></node>" ), "test" );
        self.assertEqual( jnk.get_node_label_from_config( "<node><label>test best babs</label></node>" ), "test best babs" );
        self.assertEqual( "", jnk.get_node_label_from_config( "<node><label></label></node>" ) );
        self.assertEqual( "", jnk.get_node_label_from_config( "<node><label/></node>" ) );
        self.assertEqual( "", jnk.get_node_label_from_config( "<node><blablabla/><bababa>bububu</bababa></node>" ) );
        self.assertEqual( "", jnk.get_node_label_from_config( "<node><buka><chacha/><label>baba</label></buka></node>" ) );
        self.assertEqual( jnk.get_node_label_from_config( "<node><buka><chacha/><label>baba</label></buka><label>ka</label></node>" ), "ka" );
        return;

    def test_set_node_label_in_config( self ):
        jnk = Jenkins();
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><label>bukachacha</label></node>" , "chachabuka" ) ), "<node><label>chachabuka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><label>bu ka cha cha</label></node>" , "chachabuka" ) ), "<node><label>chachabuka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><label>bu ka</label></node>" , "chachabuka" ) ), "<node><label>chachabuka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><label></label></node>" , "chachabuka" ) ), "<node><label>chachabuka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><label/></node>" , "chachabuka" ) ), "<node><label>chachabuka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node></node>" , "chachabuka" ) ), "<node><label>chachabuka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node/>" , "chachabuka" ) ), "<node><label>chachabuka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><label>bukachacha</label></node>" , "cha cha bu ka" ) ), "<node><label>cha cha bu ka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><label>bu ka cha cha</label></node>" , "cha cha bu ka" ) ), "<node><label>cha cha bu ka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><label>bu ka</label></node>" , "cha cha bu ka" ) ), "<node><label>cha cha bu ka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><label></label></node>" , "cha cha bu ka" ) ), "<node><label>cha cha bu ka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><label/></node>" , "cha cha bu ka" ) ), "<node><label>cha cha bu ka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node></node>" , "cha cha bu ka" ) ), "<node><label>cha cha bu ka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node/>" , "cha cha bu ka" ) ), "<node><label>cha cha bu ka</label></node>" );
        self.assertEqual( xml_norm( jnk.set_node_label_in_config( "<node><buka><label>ka</label></buka></node>" , "cha cha bu ka" ) ), "<node><buka><label>ka</label></buka><label>cha cha bu ka</label></node>" );
        return;

    def test_xml_job_enable( self ):
        jnk = Jenkins();
        self.assertEqual( xml_norm( jnk.job_xml_enable( "<job><name>krab</name><disabled>true</disabled><attr>ratcat</attr></job>" ) ), "<job><name>krab</name><disabled>false</disabled><attr>ratcat</attr></job>" );
        self.assertEqual( xml_norm( jnk.job_xml_enable( "<job><name>krab</name><attr>ratcat</attr></job>" ) ), "<job><name>krab</name><attr>ratcat</attr></job>" );
        self.assertEqual( xml_norm( jnk.job_xml_enable( "<job><name>krab</name><disabled>true</disabled><attr>ratcat</attr><byaka><disabled>true</disabled></byaka></job>" ) ), "<job><name>krab</name><disabled>false</disabled><attr>ratcat</attr><byaka><disabled>true</disabled></byaka></job>" );
        self.assertEqual( xml_norm( jnk.job_xml_enable( "<job/>" ) ), "<job/>" );
        return;

class NodeTestSuite( unittest.TestCase ):
    def setUp( r_self ):
        os.environ[ 'JENKINS_URL' ] = 'http://localhost:8080';

    def test_node_enable( self ):
        self.assertEqual( TestJenkinsClient().enable_node( 'testnode' ), ( posixpath.join( 'computer', 'testnode', 'enable' ), {} ) );
        return;

    def test_node_disable( self ):
        self.assertEqual( TestJenkinsClient().disable_node( 'testnode' ), ( posixpath.join( 'computer', 'testnode', 'disable' ), {} ) );
        return;


    def test_node_delete( self ):
        self.assertEqual( TestJenkinsClient().delete_node( 'testnode' ), ( posixpath.join( 'computer', 'testnode', 'doDelete' ), {} ) );
        return;

    def test_node_get_label( self ):
        jnk = TestJenkinsClient();
        self.assertEqual( jnk.get_node_label( 'testnode', '<node><label>test node off</label><name>testnode</name></node>' ), [ 'test', 'node', 'off' ] )
        self.assertEqual( jnk.get_node_label( 'testnode', '<node><label>test node off</label><name>testnode</name><pa><label>bobby must die</label></pa></node>' ), [ 'test', 'node', 'off' ] )
        self.assertEqual( [''], jnk.get_node_label( 'testnode', '<node><name>testnode</name><pa><label>bobby must die</label></pa></node>' ) )
        self.assertEqual( [''], jnk.get_node_label( 'testnode', '<node/>' ) );
        self.assertEqual( jnk.get_node_label( 'testnode' ), [ 'testnode' ] ); #configuration is to be taken from Jenkins
        return;

    def test_node_set_label( self ):
        jnk = TestJenkinsClient();
        rsp = jnk.set_node_label( 'testnode', ['bu', 'ga', 'ga'] );
        self.assertEqual( rsp[0], posixpath.join( 'computer', 'testnode', 'config.xml' ) );
        self.assertEqual( xml_norm( rsp[1][ 'data' ] ), "<node><name>testnode</name><label>bu ga ga</label></node>" );
        self.assertEqual( rsp[1][ 'params' ], None );
        self.assertEqual( rsp[1][ 'headers' ], { 'content-type' : 'application/xml' } );
        return;

class JobTestSuite( unittest.TestCase ):
    def setUp( r_self ):
        os.environ[ 'JENKINS_URL' ] = 'http://localhost:8080';

    def test_job_get( self ):
        jnk = TestJenkinsClient();
        jnk.ls_jobs_disabled.append( 'test_job' );
        jnk.dict_jobs_exist[ 'test_job' ] = None;
        self.assertEqual( xml_norm( jnk.get_job( 'test_job' ) ), "<job><name>test_job</name><disabled>true</disabled><posBuild><action><disabled>true</disabled></action></postBuild></job>" );
        jnk.dict_jobs_exist[ 'pessed_job' ] = None;
        self.assertEqual( xml_norm( jnk.get_job( 'pessed_job' ) ), "<job><name>pessed_job</name><disabled>false</disabled><posBuild><action><disabled>true</disabled></action></postBuild></job>" );
        return;

    def test_job_create( self ):
        jnk = TestJenkinsClient();

        #nonexistant
        rsp = jnk.put_job( 'nonexistant', "<job><name>nonexistant</name><disabled>false</disabled></job>" );
        self.assertEqual( rsp[0], "createItem" );
        self.assertEqual( rsp[1][ 'headers' ], {'content-type' : 'application/xml'} );
        self.assertEqual( xml_norm( rsp[1][ 'data' ] ), "<job><name>nonexistant</name><disabled>false</disabled></job>" );
        self.assertEqual( rsp[1][ 'params' ], { 'name' : 'nonexistant' } );

        #existang
        jnk.dict_jobs_exist[ 'existant' ] = None;
        rsp = jnk.put_job( 'existant', "<job><name>existant</name><disabled>false</disabled></job>" );
        self.assertEqual( rsp[0], posixpath.join( 'job', 'existant', 'config.xml' ) );
        self.assertEqual( rsp[1][ 'headers' ], {'content-type' : 'application/xml'} );
        self.assertEqual( xml_norm( rsp[1][ 'data' ] ), "<job><name>existant</name><disabled>false</disabled></job>" );
        self.assertEqual( rsp[1][ 'params' ], None );

        return;

    def test_job_delete( self ):
        self.assertEqual( TestJenkinsClient().delete_job( 'testjob' )[ 0 ], posixpath.join( 'job', 'testjob', 'doDelete' ) );
        return;

    def test_job_copy( self ):
        jnk = TestJenkinsClient();
        dict_rsp_headers = { 'content-type' : 'application/xml' };

        # 1. template = no, existant config, new
        str_job_name = "s.job.case.01.test";
        str_job_xml = "<job><name>" + str_job_name + "</name><disabled>true</disabled><command>echo lazhaa</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_xml, str_job_name, enabled = False );
        self.assertEqual( obj_resp[0], "createItem" );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertEqual( obj_resp[1][ 'params' ], { 'name' : str_job_name } );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml );

        # 2. template = no, existant config, overwrite
        str_job_name = "s.job.case.02.test";
        jnk.dict_jobs_exist[ str_job_name ] = None;
        str_job_xml = "<job><name>" + str_job_name + "</name><disabled>true</disabled><command>echo lazhaa</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_xml, str_job_name, enabled = False );
        self.assertEqual( obj_resp[0], posixpath.join( "job", str_job_name, "config.xml" ) );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertIsNone( obj_resp[1][ 'params' ] );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml );

        # 3. template = no, get config, new
        str_job_dst_name = "s.job.case.03.1.test";
        str_job_src_name = "s.job.case.03.2.test";
        jnk.dict_jobs_exist[ str_job_src_name ] = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>echo biliberda</command></job>";
        str_job_dst_xml = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>echo biliberda</command></job>";
        obj_resp = jnk.copy_job( str_job_src_name, str_job_dst_name, enabled = False );
        self.assertEqual( obj_resp[0], "createItem" );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertEqual( obj_resp[1][ 'params' ], { "name" : str_job_dst_name } );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_dst_xml );

        # 4. template = no, get config, overwrite
        str_job_dst_name = "s.job.case.03.1.test";
        str_job_src_name = "s.job.case.03.2.test";
        jnk.dict_jobs_exist[ str_job_dst_name ] = None;
        jnk.dict_jobs_exist[ str_job_src_name ] = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>echo biliberda</command></job>";
        str_job_dst_xml = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>echo biliberda</command></job>";
        obj_resp = jnk.copy_job( str_job_src_name, str_job_dst_name, enabled = False );
        self.assertEqual( obj_resp[0], posixpath.join( "job", str_job_dst_name, "config.xml" ) );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertIsNone( obj_resp[1][ 'params' ] );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_dst_xml );

        # 5. template = yes, existant config, new
        str_job_name = "s.job.case.05.test";
        str_job_xml_src = "<job><name>" + str_job_name + "</name><disabled>true</disabled><command>echo ${blablabla} ${tups}</command><report><name>report</name><disabled>true</disabled></report></job>";
        str_job_xml_dst = "<job><name>" + str_job_name + "</name><disabled>true</disabled><command>echo babs stupid shark</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_xml_src, str_job_name, parameters = { "blablabla" : "babs", "tups" : "stupid shark" }, use_template = True, enabled = False );
        self.assertEqual( obj_resp[0], "createItem" );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertEqual( obj_resp[1][ 'params' ], { 'name' : str_job_name } );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml_dst );

        # 6. template = yes, existant config, overwrite
        str_job_name = "s.job.case.06.test";
        jnk.dict_jobs_exist[ str_job_name ] = None;
        str_job_xml_src = "<job><name>" + str_job_name + "</name><disabled>true</disabled><command>echo ${blablabla} ${tups}</command><report><name>report</name><disabled>true</disabled></report></job>";
        str_job_xml_dst = "<job><name>" + str_job_name + "</name><disabled>true</disabled><command>echo babs stupid shark</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_xml_src, str_job_name, parameters = { "blablabla" : "babs", "tups" : "stupid shark" }, use_template = True, enabled = False );
        self.assertEqual( obj_resp[0], posixpath.join( "job", str_job_name, "config.xml" ) );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertIsNone( obj_resp[1][ 'params' ] );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml_dst );

        # 7. template = yes, get config, new
        str_job_src_name = "s.job.case.07.1.test";
        str_job_dst_name = "s.job.case.07.2.test";
        str_job_xml_src = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>echo ${blablabla} ${tups}</command><report><name>report</name><disabled>true</disabled></report></job>";
        jnk.dict_jobs_exist[ str_job_src_name ] = str_job_xml_src;
        str_job_xml_dst = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>echo babarobot stupid shark</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_src_name, str_job_dst_name, parameters = { "blablabla" : "babarobot", "tups" : "stupid shark" }, use_template = True, enabled = False );
        self.assertEqual( obj_resp[0], "createItem" );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertEqual( obj_resp[1][ 'params' ], { 'name' : str_job_dst_name } );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml_dst );

        # 8. template = yes, get config, overwrite
        str_job_src_name = "s.job.case.08.1.test";
        str_job_dst_name = "s.job.case.08.2.test";
        jnk.dict_jobs_exist[ str_job_dst_name ] = None;
        str_job_xml_src = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>echo ${blablabla} ${tups}</command><report><name>report</name><disabled>false</disabled></report></job>";
        jnk.dict_jobs_exist[ str_job_src_name ] = str_job_xml_src;
        str_job_xml_dst = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>echo babarobot stupid shark</command><report><name>report</name><disabled>false</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_src_name, str_job_dst_name, parameters = { "blablabla" : "babarobot", "tups" : "stupid shark" }, use_template = True, enabled = False );
        self.assertEqual( obj_resp[0], posixpath.join( "job", str_job_dst_name, "config.xml" ) );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertIsNone( obj_resp[1][ 'params' ] );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml_dst );

        # 9. template = no, existant config, new, enable disabled
        str_job_name = "s.job.case.09.test";
        str_job_xml_src = "<job><name>" + str_job_name + "</name><disabled>true</disabled><command>echo lazhaa</command><report><name>report</name><disabled>true</disabled></report></job>";
        str_job_xml_dst = "<job><name>" + str_job_name + "</name><disabled>false</disabled><command>echo lazhaa</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_xml_src, str_job_name );
        self.assertEqual( obj_resp[0], "createItem" );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertEqual( obj_resp[1][ 'params' ], { 'name' : str_job_name } );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml_dst );

        # 10. template = no, existant config, overwrite, enable disabled
        str_job_name = "s.job.case.10.test";
        jnk.dict_jobs_exist[ str_job_name ] = None;
        str_job_xml_src = "<job><name>" + str_job_name + "</name><disabled>true</disabled><command>echo lazhaa</command><report><name>report</name><disabled>true</disabled></report></job>";
        str_job_xml_dst = "<job><name>" + str_job_name + "</name><disabled>false</disabled><command>echo lazhaa</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_xml_src, str_job_name );
        self.assertEqual( obj_resp[0], posixpath.join( "job", str_job_name, "config.xml" ) );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertIsNone( obj_resp[1][ 'params' ] );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml_dst );

        # 11. template = no, get config, new, enable disabled
        str_job_dst_name = "s.job.case.11.1.test";
        str_job_src_name = "s.job.case.11.2.test";
        jnk.dict_jobs_exist[ str_job_src_name ] = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>echo biliberda</command></job>";
        str_job_dst_xml = "<job><name>" + str_job_src_name + "</name><disabled>false</disabled><command>echo biliberda</command></job>";
        obj_resp = jnk.copy_job( str_job_src_name, str_job_dst_name );
        self.assertEqual( obj_resp[0], "createItem" );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertEqual( obj_resp[1][ 'params' ], { "name" : str_job_dst_name } );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_dst_xml );

        # 12. template = no, get config, overwrite, enable disabled
        str_job_dst_name = "s.job.case.12.1.test";
        str_job_src_name = "s.job.case.12.2.test";
        jnk.dict_jobs_exist[ str_job_dst_name ] = None;
        jnk.dict_jobs_exist[ str_job_src_name ] = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>echo biliberda</command><report><name>report</name><disabled>true</disabled></report></job>";
        str_job_dst_xml = "<job><name>" + str_job_src_name + "</name><disabled>false</disabled><command>echo biliberda</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_src_name, str_job_dst_name );
        self.assertEqual( obj_resp[0], posixpath.join( "job", str_job_dst_name, "config.xml" ) );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertIsNone( obj_resp[1][ 'params' ] );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_dst_xml );

        # 13. template = yes, existant config, new, enable disabled
        str_job_name = "s.job.case.13.test";
        str_job_xml_src = "<job><name>" + str_job_name + "</name><disabled>true</disabled><command>echo ${taps} ${tups}</command><report><name>report</name><disabled>true</disabled></report></job>";
        str_job_xml_dst = "<job><name>" + str_job_name + "</name><disabled>false</disabled><command>echo cant pencil stupid shark</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_xml_src, str_job_name, parameters = { "taps" : "cant pencil", "tups" : "stupid shark" }, use_template = True );
        self.assertEqual( obj_resp[0], "createItem" );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertEqual( obj_resp[1][ 'params' ], { 'name' : str_job_name } );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml_dst );

        # 14. template = yes, existant config, overwrite, enable disabled
        str_job_name = "s.job.case.14.test";
        jnk.dict_jobs_exist[ str_job_name ] = None;
        str_job_xml_src = "<job><name>" + str_job_name + "</name><disabled>true</disabled><command>echo ${blablabla} ${tups}</command><report><name>report</name><disabled>true</disabled></report></job>";
        str_job_xml_dst = "<job><name>" + str_job_name + "</name><disabled>false</disabled><command>echo babs stupid shark</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_xml_src, str_job_name, parameters = { "blablabla" : "babs", "tups" : "stupid shark" }, use_template = True );
        self.assertEqual( obj_resp[0], posixpath.join( "job", str_job_name, "config.xml" ) );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertIsNone( obj_resp[1][ 'params' ] );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml_dst );

        # 15. template = yes, get config, new
        str_job_src_name = "s.job.case.15.1.test";
        str_job_dst_name = "s.job.case.15.2.test";
        str_job_xml_src = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>python2.7 ${faak}.py ${tups}.py</command><report><name>report</name><disabled>true</disabled></report></job>";
        jnk.dict_jobs_exist[ str_job_src_name ] = str_job_xml_src;
        str_job_xml_dst = "<job><name>" + str_job_src_name + "</name><disabled>false</disabled><command>python2.7 pussy pig.py stupid shark.py</command><report><name>report</name><disabled>true</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_src_name, str_job_dst_name, parameters = { "faak" : "pussy pig", "tups" : "stupid shark" }, use_template = True );
        self.assertEqual( obj_resp[0], "createItem" );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertEqual( obj_resp[1][ 'params' ], { 'name' : str_job_dst_name } );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml_dst );

        # 16. template = yes, get config, overwrite
        str_job_src_name = "s.job.case.16.1.test";
        str_job_dst_name = "s.job.case.16.2.test";
        jnk.dict_jobs_exist[ str_job_dst_name ] = None;
        str_job_xml_src = "<job><name>" + str_job_src_name + "</name><disabled>true</disabled><command>python2.7 ${kill_them_all}.py ${dirty_bugs}</command><report><name>report</name><disabled>false</disabled></report></job>";
        jnk.dict_jobs_exist[ str_job_src_name ] = str_job_xml_src;
        str_job_xml_dst = "<job><name>" + str_job_src_name + "</name><disabled>false</disabled><command>python2.7 be_nice_gay.py --destroy-brain=True</command><report><name>report</name><disabled>false</disabled></report></job>";
        obj_resp = jnk.copy_job( str_job_src_name, str_job_dst_name, parameters = { "kill_them_all" : "be_nice_gay", "dirty_bugs" : "--destroy-brain=True" }, use_template = True );
        self.assertEqual( obj_resp[0], posixpath.join( "job", str_job_dst_name, "config.xml" ) );
        self.assertEqual( obj_resp[1][ 'headers' ], dict_rsp_headers );
        self.assertIsNone( obj_resp[1][ 'params' ] );
        self.assertEqual( xml_norm( obj_resp[1][ 'data' ] ), str_job_xml_dst );
        return;

    def test_job_enable( self ):
        self.assertEqual( TestJenkinsClient().enable_job( 'testjob' )[ 0 ], posixpath.join( 'job', 'testjob', 'enable' ) );
        return;

    def test_job_disable( self ):
        self.assertEqual( TestJenkinsClient().disable_job( 'testjob' )[ 0 ], posixpath.join( 'job', 'testjob', 'disable' ) );
        return;

    def test_list_builds( self ):
        ## test for single node
        result = TestJenkinsClient().list_builds( 'test-node' );
        self.assertIn( "test-node", result );
        self.assertEqual( len( result[ "test-node" ] ), 1 );
        self.assertEqual( result[ "test-node" ][0][ "job_name" ], "c.TEST_CUSTOMER.branches-test.test" );
        self.assertEqual( result[ "test-node" ][0][ "build_nubmer" ], 27 );
        ## test for system-wide
        result = TestJenkinsClient().list_builds();
        self.assertIn( "test-node", result );
        self.assertEqual( len( result[ "test-node" ] ), 1 );
        self.assertEqual( result[ "test-node" ][0][ "job_name" ], "c.TEST_CUSTOMER.branches-test.test" );
        self.assertEqual( result[ "test-node" ][0][ "build_nubmer" ], 27 );
        self.assertIn( "other-node", result );
        self.assertEqual( len( result[ "other-node" ] ), 1 );
        self.assertEqual( result[ "other-node" ][0][ "job_name" ], "c.TEST_CUSTOMER.trunk.test" );
        self.assertEqual( result[ "other-node" ][0][ "build_nubmer" ], 3 );
        return;

    def test_list_queue( self ):
        result = TestJenkinsClient().list_queue();
        self.assertEqual( len( result ), 2 );
        jobnames = map( lambda x: x.job_name, result );
        self.assertIn( "c.OWI_LUXCTRL.branches-int.cards", jobnames );
        self.assertIn( "tech.selfcheck", jobnames );
        jobids = map( lambda x: x.queue_id, result );
        self.assertIn( 9590, jobids);
        self.assertIn( 9559, jobids);

    def test_unqueue( self ):
        jnk = TestJenkinsClient();
        jnk.unqueue_item( 1234 );

        self.assertEqual( jnk.last_post_url, posixpath.join( 'queue', 'cancelItem' ) );
        self.assertEqual( jnk.last_post_data[ "params" ][ "id" ], 1234 );
        self.assertEqual( jnk.last_post_data[ "data" ], dict() );

    def test_list_node( self ):
        jnk = TestJenkinsClient();
        result = jnk.list_nodes();

        for str_node in jnk.computer_data.keys():
            self.assertIn( str_node, result );


