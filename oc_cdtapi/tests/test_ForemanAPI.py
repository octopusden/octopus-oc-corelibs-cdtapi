#!/usr/bin/python2.7

import sys
#if sys.version[0]=='3':
#    from io import StringIO
#else:
#    import StringIO
import re
import json
import unittest
from datetime import datetime, timedelta
from collections import namedtuple
from oc_cdtapi.ForemanAPI import ForemanAPI, ForemanAPIError

class _Response(object):
    """
    Fake response object
    """

    def __init__(self, data):
        self.content = data
        self.text = json.dumps({"results": [{"id": 100, "name": "test_stand"}]}) 
        self.status_code = 200

    def json(self):
        return json.loads(self.content)


class _Session(object):
    """
    Fake requests session
    """

    def __init__(self, handler):
        self.handler = handler

    def get(self, req, params = None, **other):
        r = req
        if params is not None and len(params) > 0:
            r += '?' + '&'.join(map(lambda x: x [0]+'='+x [1], params.items()))
        return _Response(self.handler(r))

    def post(self, req, params = None, **other):
        r = req
        if params is not None and len(params) > 0:
            r += '?' + '&'.join(map(lambda x: x [0]+'='+x [1], params.items()))
        return _Response(self.handler(r))
    
    def delete(self, req, params = None, **other):
        r = req
        if params is not None and len(params) > 0:
            r += '?' + '&'.join(map(lambda x: x [0]+'='+x [1], params.items()))
        return _Response(self.handler(r))

    def put(self, req, params = None, **other):
        return _Response(self.handler(req))

class _ForemanAPI(ForemanAPI):

    def __init__(self, *args, **argv):
        self.web = _Session(self._read_url)
        self.root = "https://foreman"
        class_defaults = namedtuple("values", "exp_date location_id hostgroup deploy_on")
        exp_date = "01/01/2030"
        location_id = 5
        hostgroup = 11
        deploy_on = 1
        
        self.defs = class_defaults(exp_date, location_id, hostgroup, deploy_on)
        self.apiversion = 1

    def _read_url(self,url):
        """
        Overrides http request method
        """
        if re.match('.+\/hosts/test$',url):
            return '{"name": "test_stand", "uuid": "50391e80-afde-c4a5-c562-e5af02e5e449"}'
        elif re.match('.+\/hosts/test2$',url):
            return '{"name": "test_stand_2"}'
        elif re.match('.+\/puppetclasses/test_class', url):
            return '{"id": 101}'
        elif re.match('.+\/smart_class_parameters/1111', url):
            return '{"value": "default"}'
        elif re.match('.+\/hostgroups/1/puppetclasses', url):
            return '{"name": "puppet"}'
        elif re.match('.+\/subnets', url):
            return '{"total": 1, "subnetname": 64}'
        elif re.match('.+\/hosts/test/config_reports$', url):
            return '{"report_id": 102}'
        elif re.match('.+\/config_reports/101', url):
            return '{"result": "Success"}'
        elif re.match('.+\/usergroups.*%22.+%22$', url):
            return '{"results": [{"name":"NEW QA","id":2}]}'
        elif re.match('.+\/hostgroups$', url):
            return '{"results": [{"name":"docker-host","id":3}]}'
        elif re.match ('.+\/hosts\/test-host-name.*', url):
            return '{"result": "Success"}'
        elif re.match('.+\/organizations', url):
            return '{"total": 1, "results": [{"name": "CompanyName", "id": 1}]}'
        elif re.match('.+\/operatingsystems$', url):
            return '{"total": 1, "results": [{"description": "CentOS 7 Test", "id": 1}]}'
        elif re.match('.+\/operatingsystems/1/images$', url):
            return '{"total": 1, "results": [{"name": "CentOS 7.9", "uuid": "03366eb2-fc38-4813-970d-bd66c0b4cbf4"}]}'
        elif re.match('.+\/compute_resources/1/available_flavors$', url):
            return '{"total": 1, "results": [{"name": "cdt.1.4", "id": "13c5cccf-f907-4861-b367-bee86bec47cd"}]}'
        elif re.match('.+\/compute_resources/1$', url):
            return '{"description": "Test Provider", "compute_attributes": [{"attributes": {"tenant_id": "aeea0ca2b1ab449e86fd7b4295455ecf"}}]}'
        elif re.match('.+\/compute_resources/2$', url):
            return '{"description": "Test Provider", "compute_attributes": [{"attributes": {"availability_zone": "nova"}}]}'
        return '[]'

class TestForemanAPI(unittest.TestCase):

    def setUp(self):
        self.api = _ForemanAPI()
        self.json_object = json.dumps({"name": "custom_name_test", "is_owned_by": 100})
    
    def test_get_usergroup_id(self):
        group_id = self.api.get_usergroup_id("NEW QA")
        self.assertEqual(group_id, 2)

    def test_get_owner(self):
        user = self.api.get_owner("test")
        self.assertEqual(user, 100)

    def test_set_expiration(self):
        exp_date = self.api._set_expiration()
        self.assertEqual(exp_date, str((datetime.now() + timedelta(days=90)).strftime('%d/%m/%Y')))

    def test_create_host_no_hostname(self):
        with self.assertRaises(ForemanAPIError) as err:
            self.api.create_host()

    def test_create_host_default_values_no(self):
        with self.assertRaises(ForemanAPIError):
            self.api.create_host("test")

    def test_create_host_correct_values(self):
        try:
            self.api.create_host(custom_json=self.json_object)
        except ForemanAPIError:
            raise

    def test_get_host_info(self):
        info = self.api.get_host_info("test")
        self.assertEqual(info["name"], "test_stand")

    def test_get_host_info_unknown_host(self):
        info = self.api.get_host_info("test1")
        self.assertFalse(isinstance(info, dict))

    def test_puppet_class_info(self):
        info = self.api.puppet_class_info("test_class")
        self.assertEqual(info["id"], 101)

    def test_smart_class_info(self):
        info = self.api.smart_class_info(1111)
        self.assertEqual(info["value"], "default")

    def test_get_hostgroup_puppetclasses(self):
        classes = self.api.get_hostgroup_puppetclasses(1)
        self.assertEqual(classes["name"], "puppet")

    def test_get_subnets(self):
        subnets = self.api.get_subnets()
        self.assertEqual(subnets["subnetname"], 64)
    
    def test_get_host_reports(self):
        reports = self.api.get_host_reports("test")
        self.assertEqual(reports["report_id"], 102)
    
    def test_get_report(self):
        report = self.api.get_report(101)
        self.assertEqual(report["result"], "Success")
    
    def test_delete_host(self):
        try:
            self.api.delete_host("test")
        except ForemanAPIError:
            raise

    def test_hostgroup_found(self):
        hostgroup_id = self.api.get_hostgroup_id("docker-host")
        self.assertEqual(hostgroup_id, 3)
    
    def test_hostgroup_not_found(self):
        hostgroup_id = self.api.get_hostgroup_id("docker")
        self.assertEqual(hostgroup_id, None)

    def test_get_organization_id(self):
        organization_id = self.api.get_organization_id("CompanyName")
        self.assertEqual(organization_id, 1)

    def test_get_organization_id_not_found(self):
        organization_id = self.api.get_organization_id("CompanyName2")
        self.assertIsNone(organization_id)
    
    def test_set_host_expiry(self):
        self.api.set_host_expiry('test-host-name','2222-01-22')

    def test_get_image_uuid(self):
        uuid = self.api.get_image_uuid("CentOS 7 Test", "CentOS 7.9")
        self.assertEqual("03366eb2-fc38-4813-970d-bd66c0b4cbf4", uuid)
    
    def test_get_image_uuid_not_found(self):
        uuid = self.api.get_image_uuid("CentOS 7", "CentOS 7")
        self.assertIsNone(uuid)
    
    def test_get_flavor_id(self):
        flavor_id = self.api.get_flavor_id(1, "cdt.1.4")
        self.assertEqual("13c5cccf-f907-4861-b367-bee86bec47cd", flavor_id)
    
    def test_get_flavor_id_not_found(self):
        flavor_id = self.api.get_flavor_id(1, "cdt.1.5")
        self.assertIsNone(flavor_id)
    
    def test_get_tenant_id(self):
        tenant_id = self.api.get_tenant_id(1)
        self.assertEqual("aeea0ca2b1ab449e86fd7b4295455ecf", tenant_id)
    
    def test_get_tenant_id_not_found(self):
        tenant_id = self.api.get_tenant_id(2)
        self.assertIsNone(tenant_id)
    
    def test_get_host_uuid(self):
        uuid = self.api.get_host_uuid("test")
        self.assertEqual("50391e80-afde-c4a5-c562-e5af02e5e449", uuid)
    
    def test_get_host_uuid(self):
        uuid = self.api.get_host_uuid("test2")
        self.assertIsNone(uuid)

