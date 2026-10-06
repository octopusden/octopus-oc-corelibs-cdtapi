#!/usr/bin/python3

import re
import json
import unittest
from unittest.mock import patch, MagicMock, call, PropertyMock
from datetime import datetime, timedelta
from collections import namedtuple
from oc_cdtapi.ForemanAPI import ForemanAPI, ForemanAPIError, HostComputeAttributes, PartitionUsage

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
        self.root = "https://foreman.example.com"
        class_defaults = namedtuple("values", "exp_date location_id hostgroup deploy_on")
        exp_date = "01/01/2030"
        location_id = 5
        hostgroup = 11
        deploy_on = 1

        self.defs = class_defaults(exp_date, location_id, hostgroup, deploy_on)
        self.__apiversion = 1
        self.__foreman_version = None
        self.__foreman_version_major = None

    def _read_url(self,url):
        """
        Overrides http request method
        """
        if re.match('.+\/hosts/test$',url):
            return '{"name": "test_stand", "uuid": "50391e80-afde-c4a5-c562-e5af02e5e449"}'
        elif re.match('.+\/hosts/test2$',url):
            return '{"name": "test_stand_2"}'
        elif re.match('.+\/hosts/test-parameter$',url):
            return '{"name": "test_parameter", "parameters": [{"name": "client-code", "value": "_TEST"}, {"name": "client-region", "value": "EARTH"}]}'
        elif re.match('.+\/status', url):
            return '{"result":"ok","status":200,"version":"2.5.4","api_version":2}'
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
        elif re.match('.+\/vm_compute_attributes', url):
            return '{"volumes_attributes": {"0": {"size_gb": 100}}}'
        elif re.match('.+\/job_templates', url):
            return '{"results": [{"id": 215, "name": "Run \\"cdt-resize-partition\\" role CDT"}]}'
        elif re.match('.+\/job_invocations/999', url):
            return '{"succeeded": 1, "pending": 0}'
        elif re.match(r'.+/job_invocations\?search=host=test-ansible-vm-empty', url):
            return '{"results": []}'
        elif re.match(r'.+/job_invocations\?search=host=test-ansible-vm', url):
            return '{"results": [{"id": 1000, "status": 0, "status_label": "succeeded"}]}'
        elif re.match('.+\/job_invocations', url):
            return '{"id": 999, "status": "ok"}'
        return '[]'

def _mock_response(data, status_code=200):
    """
    MagicMock response returning data from json()
    """
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = data
    return response

def _vm_compute_attributes(**fields):
    """
    vm_compute_attributes response of a VMware host (fog-vsphere shape), with the given fields set
    """
    data = {
        "cpus": 2,
        "memory_mb": 4096,
        "power_state": "poweredOn",
        "name": "test-vm",
        "volumes_attributes": {"0": {"name": "Hard disk 1", "size_gb": 40}}
    }
    data.update(fields)
    return data

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
        self.api.create_host(custom_json=self.json_object)

    def test_get_host_info(self):
        info = self.api.get_host_info("test")
        self.assertEqual(info["name"], "test_stand")

    def test_get_host_info_unknown_host(self):
        info = self.api.get_host_info("test1")
        self.assertFalse(isinstance(info, dict))

    def test_foreman_version(self):
        self.assertEqual(self.api.foreman_version, "2.5.4")

    #TODO: unmark and re-factor when tests for 'ForemanAPI.apiversion==2' will be created
    @unittest.expectedFailure
    def test_foreman_apiversion(self):
        self.assertEqual(self.api.apiversion, 2)

    def test_foreman_version_major(self):
        self.assertEqual(self.api.foreman_version_major, 2)

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

    def test_get_host_disk_size(self):
        disk_size = self.api.get_host_disk_size("test2")
        self.assertEqual(disk_size, 100)

    @patch.object(ForemanAPI, 'get')
    def test_get_host_memory_mb(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "cpus": 1,
            "memory_mb": 5120,
            "guest_id": "other5xLinux64Guest",
            "path": "test-path",
            "datacenter": "test-dc",
            "cluster": "test-cl",
            "resource_pool": "test-rp",
            "name": "test-vm",
            "uuid": "test-vm-uuid"
        }

        mock_get.return_value = mock_response

        memory_mb = self.api.get_host_memory_mb("test-host-ansible-roles")
        self.assertEqual(memory_mb, 5120)

    @patch.object(ForemanAPI, 'get')
    def test_get_host_compute_attributes(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "cpus": 1,
            "memory_mb": 5120,
            "guest_id": "other5xLinux64Guest",
            "path": "test-path",
            "datacenter": "test-dc",
            "cluster": "test-cl",
            "resource_pool": "test-rp",
            "power_state": "poweredOff",
            "name": "test-vm",
            "uuid": "test-vm-uuid",
            "volumes_attributes": {
                "0": {
                    "thin": True,
                    "name": "Hard disk 1",
                    "mode": "persistent",
                    "id": "dsfb-4f0b-6d21-867f-baf4e4941c27",
                    "eager_zero": False,
                    "filename": "[datastore] 34543dfgdfg03/sandbox",
                    "size": 104857600,
                    "key": 2000,
                    "unit_number": 0,
                    "controller_key": 1000,
                    "size_gb": 100
                }
            }
        }

        mock_get.return_value = mock_response

        result = self.api.get_host_compute_attributes("test-host-ansible-roles")
        self.assertEqual(result.cpus, 1)
        self.assertEqual(result.power_state, "poweredOff")
        self.assertEqual(result.memory_mb, 5120)
        self.assertEqual(result.disk_size, 100)

    @patch.object(ForemanAPI, 'get')
    def test_get_host_compute_attributes_partitions(self, mock_get):
        mock_get.return_value = _mock_response(_vm_compute_attributes(partitions=[
            {"path": "/", "free": 2147483648, "capacity": 10737418240},
            {"path": "/local", "free": 1073741824, "capacity": 21474836480}
        ]))

        result = self.api.get_host_compute_attributes("host.example")

        mock_get.assert_called_once_with("hosts/host.example/vm_compute_attributes")
        self.assertEqual(result.partitions, [
            PartitionUsage(path="/", capacity=10737418240, free=2147483648),
            PartitionUsage(path="/local", capacity=21474836480, free=1073741824),
        ])
        self.assertEqual([partition.used_percent for partition in result.partitions], [80.0, 95.0])
        self.assertIsInstance(result.partitions[0].used_percent, float)
        self.assertEqual(result.power_state, "poweredOn")
        self.assertEqual(result.disk_size, 40)

    @patch.object(ForemanAPI, 'get')
    def test_get_host_compute_attributes_without_partitions(self, mock_get):
        # powered-off VMs and VMs without VMware Tools report no partitions
        responses = {
            "no key": _vm_compute_attributes(power_state="poweredOff"),
            "null": _vm_compute_attributes(power_state="poweredOff", partitions=None),
            "empty list": _vm_compute_attributes(power_state="poweredOff", partitions=[]),
        }
        for case, data in responses.items():
            with self.subTest(case=case):
                mock_get.return_value = _mock_response(data)

                result = self.api.get_host_compute_attributes("host.example")

                self.assertIsNone(result.partitions)
                self.assertEqual(result.power_state, "poweredOff")
                self.assertEqual(result.disk_size, 40)

    @patch.object(ForemanAPI, 'get')
    def test_get_host_compute_attributes_without_compute_resource(self, mock_get):
        for data in ({}, None):
            with self.subTest(data=data):
                mock_get.return_value = _mock_response(data)

                result = self.api.get_host_compute_attributes("host.example")

                self.assertEqual(result, HostComputeAttributes(None, None, None, None))
                self.assertIsNone(result.partitions)

    @patch.object(ForemanAPI, 'get')
    def test_get_host_compute_attributes_malformed_partitions(self, mock_get):
        mock_get.return_value = _mock_response(_vm_compute_attributes(partitions=[
            {"free": 1073741824, "capacity": 10737418240},
            {"path": "", "free": 1073741824, "capacity": 10737418240},
            "not-a-partition",
            {"path": "/boot", "free": 1073741824},
            {"path": "/var", "free": 0, "capacity": 0},
            {"path": "/srv", "capacity": 1073741824},
            {"path": "/opt", "free": "n/a", "capacity": "unknown"},
            {"path": "/tmp", "free": "536870912", "capacity": "1073741824"}
        ]))

        result = self.api.get_host_compute_attributes("host.example")

        # entries without a path are skipped, the others are kept
        self.assertEqual([partition.path for partition in result.partitions], ["/boot", "/var", "/srv", "/opt", "/tmp"])
        self.assertEqual([partition.used_percent for partition in result.partitions], [None, None, None, None, 50.0])
        self.assertEqual(result.partitions[3], PartitionUsage(path="/opt", capacity=None, free=None))
        self.assertEqual(result.partitions[4], PartitionUsage(path="/tmp", capacity=1073741824, free=536870912))

    def test_host_compute_attributes_unusable_partitions(self):
        # no usable entry, or not a list at all
        for partitions in ([{"capacity": 10737418240}, None], {"path": "/"}, "/"):
            with self.subTest(partitions=partitions):
                result = HostComputeAttributes.from_json(_vm_compute_attributes(partitions=partitions))

                self.assertIsNone(result.partitions)
                self.assertEqual(result.power_state, "poweredOn")

    def test_host_compute_attributes_positional_arguments(self):
        attributes = HostComputeAttributes(2, 4096, 40, "poweredOn")

        self.assertEqual(attributes.cpus, 2)
        self.assertEqual(attributes.memory_mb, 4096)
        self.assertEqual(attributes.disk_size, 40)
        self.assertEqual(attributes.power_state, "poweredOn")
        self.assertIsNone(attributes.partitions)
        self.assertEqual(attributes.to_json(), {
            "cpus": 2,
            "memory_mb": 4096,
            "disk_size": 40,
            "power_state": "poweredOn",
            "partitions": None
        })

    def test_host_compute_attributes_to_json_with_partitions(self):
        partitions = [{"path": "/", "free": 2147483648, "capacity": 10737418240}]
        attributes = HostComputeAttributes.from_json(_vm_compute_attributes(partitions=partitions))

        self.assertEqual(attributes.to_json(), {
            "cpus": 2,
            "memory_mb": 4096,
            "disk_size": 40,
            "power_state": "poweredOn",
            "partitions": partitions
        })
        # the JSON partitions read back to the same objects
        self.assertEqual(HostComputeAttributes.from_json(attributes.to_json()).partitions, attributes.partitions)

    def test_get_job_template_id(self):
        response = self.api.get_job_template_id("Run \"cdt-resize-partition\" role CDT")
        self.assertEqual(response, 215)

    def test_send_job_invocation(self):
        self.api.send_job_invocation("resize_partition", "test-vm")

    def test_is_job_invocation_success(self):
        status = self.api.is_job_invocation_success("999")
        self.assertTrue(status)

    def test_set_host_owner(self):
        self.api.set_host_owner('test-host-name', 'user1')

    def test_set_backup_policy(self):
        self.api.set_backup_policy('test-host-name','WEEKLY_NO_DR')

    def test_get_parameter_value(self):
        response = self.api.get_parameter_value("test-parameter", "client-code")
        self.assertEqual(response, {"client-code": "_TEST"})

    def test_get_multiple_parameter_value(self):
        response = self.api.get_parameter_value("test-parameter", ["client-code", "client-region", "test"])
        self.assertEqual(response, {"client-code": "_TEST", "client-region": "EARTH"})

    def test_get_parameter_value_empty(self):
        value = self.api.get_parameter_value("test-parameter", "client-name")
        self.assertIsNone(value)

    def test_set_parameter_value(self):
        self.api.set_parameter_value("test-parameter", "test-name", "test-value")

    @patch.object(ForemanAPI, 'get')
    def test_get_host_ansible_roles(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC" },
            { "id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
        ]

        mock_get.return_value = mock_response

        roles = self.api.get_host_ansible_roles("test-host-ansible-roles")
        self.assertEqual(roles, [{"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC" }, { "id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}])

    @patch.object(ForemanAPI, 'get')
    def test_get_ansible_role_all(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results":  [
                {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
                {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
            ]
        }

        mock_get.return_value = mock_response

        roles = self.api.get_ansible_role()

        mock_get.assert_called_once_with(
            "ansible/api/ansible_roles",
            headers=self.api.headers,
            params={'per_page': 'all'}
        )
        self.assertEqual(roles, [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
        ])

    @patch.object(ForemanAPI, 'get')
    def test_get_ansible_role_single_string(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results":  [
                {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            ]
        }

        mock_get.return_value = mock_response

        roles = self.api.get_ansible_role("roles-one")

        mock_get.assert_called_once_with(
            "ansible/api/ansible_roles",
            params={'search': 'name=roles-one'},
            headers=self.api.headers
        )
        self.assertEqual(roles, [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
        ])

    @patch.object(ForemanAPI, 'get')
    def test_get_ansible_role_single_int(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results":  [
                {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            ]
        }

        mock_get.return_value = mock_response

        roles = self.api.get_ansible_role(51)

        mock_get.assert_called_once_with(
            "ansible/api/ansible_roles",
            params={'search': 'id=51'},
            headers=self.api.headers
        )
        self.assertEqual(roles, [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
        ])

    @patch.object(ForemanAPI, 'get')
    def test_get_ansible_role_list_string(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results":  [
                {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
                {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
            ]
        }

        mock_get.return_value = mock_response

        roles = self.api.get_ansible_role(["roles-one", "roles-two"])

        mock_get.assert_called_once_with(
            "ansible/api/ansible_roles",
            params={'search': 'name=roles-one or name=roles-two'},
            headers=self.api.headers
        )
        self.assertEqual(roles, [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
        ])

    @patch.object(ForemanAPI, 'get')
    def test_get_ansible_role_list_int(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results":  [
                {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
                {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
            ]
        }

        mock_get.return_value = mock_response

        roles = self.api.get_ansible_role([51, 53])

        mock_get.assert_called_once_with(
            "ansible/api/ansible_roles",
            params={'search': 'id=51 or id=53'},
            headers=self.api.headers
        )
        self.assertEqual(roles, [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
        ])

    @patch.object(ForemanAPI, 'get')
    def test_get_ansible_role_list_mixed(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results":  [
                {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
                {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
            ]
        }

        mock_get.return_value = mock_response

        roles = self.api.get_ansible_role([51, "roles-two"])

        mock_get.assert_called_once_with(
            "ansible/api/ansible_roles",
            params={'search': 'id=51 or name=roles-two'},
            headers=self.api.headers
        )
        self.assertEqual(roles, [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
        ])

    @patch.object(ForemanAPI, 'get_ansible_role')
    @patch.object(ForemanAPI, 'post')
    def test_assign_ansible_roles_string(self, mock_post, mock_get_ansible_role):
        mock_get_ansible_role.return_value = [{"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"}]
        mock_post.return_value = None

        self.api.assign_ansible_roles("test-host-name", "roles-one")

        mock_get_ansible_role.assert_called_once_with(["roles-one"])

        payload = {
            "ansible_role_ids": [51]
        }
        mock_post.assert_called_once_with(
            "hosts/test-host-name/assign_ansible_roles",
            headers=self.api.headers,
            json=payload
        )

    @patch.object(ForemanAPI, 'get_ansible_role')
    @patch.object(ForemanAPI, 'post')
    def test_assign_ansible_roles_int(self, mock_post, mock_get_ansible_role):
        mock_get_ansible_role.return_value = [{"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"}]
        mock_post.return_value = None

        self.api.assign_ansible_roles("test-host-name", 51)

        mock_get_ansible_role.assert_called_once_with([51])

        payload = {
            "ansible_role_ids": [51]
        }
        mock_post.assert_called_once_with(
            "hosts/test-host-name/assign_ansible_roles",
            headers=self.api.headers,
            json=payload
        )

    @patch.object(ForemanAPI, 'get_ansible_role')
    @patch.object(ForemanAPI, 'post')
    def test_assign_ansible_roles_list_string(self, mock_post, mock_get_ansible_role):
        mock_get_ansible_role.return_value = [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
        ]
        mock_post.return_value = None

        self.api.assign_ansible_roles("test-host-name", ["roles-one", "roles-two"])

        mock_get_ansible_role.assert_called_once_with(["roles-one", "roles-two"])

        payload = {
            "ansible_role_ids": [51, 53]
        }
        mock_post.assert_called_once_with(
            "hosts/test-host-name/assign_ansible_roles",
            headers=self.api.headers,
            json=payload
        )

    @patch.object(ForemanAPI, 'get_ansible_role')
    @patch.object(ForemanAPI, 'post')
    def test_assign_ansible_roles_list_int(self, mock_post, mock_get_ansible_role):
        mock_get_ansible_role.return_value = [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
        ]
        mock_post.return_value = None

        self.api.assign_ansible_roles("test-host-name", [51, 53])

        mock_get_ansible_role.assert_called_once_with([51, 53])

        payload = {
            "ansible_role_ids": [51, 53]
        }
        mock_post.assert_called_once_with(
            "hosts/test-host-name/assign_ansible_roles",
            headers=self.api.headers,
            json=payload
        )

    @patch.object(ForemanAPI, 'get_ansible_role')
    @patch.object(ForemanAPI, 'post')
    def test_assign_ansible_roles_list_random(self, mock_post, mock_get_ansible_role):
        mock_get_ansible_role.return_value = [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
        ]
        mock_post.return_value = None

        self.api.assign_ansible_roles("test-host-name", ["roles-one", 53])

        mock_get_ansible_role.assert_called_once_with(["roles-one", 53])

        payload = {
            "ansible_role_ids": [51, 53]
        }
        mock_post.assert_called_once_with(
            "hosts/test-host-name/assign_ansible_roles",
            headers=self.api.headers,
            json=payload
        )

    @patch.object(ForemanAPI, 'get_ansible_role')
    @patch.object(ForemanAPI, 'post')
    def test_assign_ansible_roles_preserves_requested_order(self, mock_post, mock_get_ansible_role):
        mock_get_ansible_role.return_value = [
            {"id": 51, "name": "roles-one"},
            {"id": 52, "name": "roles-two"},
            {"id": 53, "name": "roles-three"},
        ]
        mock_post.return_value = None

        self.api.assign_ansible_roles(
            "test-host-name", ["roles-two", "roles-one", "roles-three"])

        payload = {
            "ansible_role_ids": [52, 51, 53]
        }
        mock_post.assert_called_once_with(
            "hosts/test-host-name/assign_ansible_roles",
            headers=self.api.headers,
            json=payload
        )

    @patch.object(ForemanAPI, 'get_ansible_role')
    @patch.object(ForemanAPI, 'post')
    @patch.object(ForemanAPI, 'get')
    def test_assign_ansible_roles_and_override(self, mock_get, mock_post, mock_get_ansible_role):
        # Mock post (1 assign + 4 overrides)
        mock_post.return_value = MagicMock()

        # Mock self.get
        get_variable_one = MagicMock()
        get_variable_one.json.return_value = {
            "results": [
                {"parameter": "version", "id": 1},
                {"parameter": "extras", "id": 2},
                {"parameter": "another-extras", "id": 3},
            ]
        }

        get_variable_two = MagicMock()
        get_variable_two.json.return_value = {
            "results": [
                {"parameter": "version", "id": 4},
                {"parameter": "extras",  "id": 5},
                {"parameter": "another-extras", "id": 6},
            ]
        }

        mock_get.side_effect = [get_variable_one, get_variable_two]

        mock_get_ansible_role.return_value = [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
        ]

        payload = {
            "roles-one": {"version": "1.2.3", "extras": "random"},
            "roles-two": {"version": "1.2.3","another-extras": "random"}
        }

        self.api.assign_ansible_roles_and_override("test-host-name", payload)

        mock_get_ansible_role.assert_called_once_with(['roles-one', 'roles-two'])

        expected_get_calls = [
            call(
                "ansible/api/ansible_variables",
                params={"search": "ansible_role=roles-one", "per_page": "all"}
            ),
            call(
                "ansible/api/ansible_variables",
                params={"search": "ansible_role=roles-two", "per_page": "all"}
            )
        ]
        mock_get.assert_has_calls(expected_get_calls, any_order=False)
        self.assertEqual(mock_get.call_count, 2)

        # Verify post called 5 times (1 assign + 4 overrides)
        self.assertEqual(mock_post.call_count, 5)

        # Verify first post call (assign ansible roles)
        first_post_call = mock_post.call_args_list[0]
        self.assertEqual(first_post_call[0][0], "hosts/test-host-name/assign_ansible_roles")
        self.assertEqual(first_post_call[1]['json'], {"ansible_role_ids": [51, 53]})

        # Verify override calls
        override_calls = mock_post.call_args_list[1:]
        self.assertEqual(len(override_calls), 4)

        self.assertIn("1-version", str(override_calls[0]))
        self.assertIn("1.2.3", str(override_calls[0]))
        self.assertIn("2-extras", str(override_calls[1]))
        self.assertIn("random", str(override_calls[1]))
        self.assertIn("4-version", str(override_calls[2]))
        self.assertIn("1.2.3", str(override_calls[2]))
        self.assertIn("6-another-extras", str(override_calls[3]))
        self.assertIn("random", str(override_calls[3]))

    @patch.object(ForemanAPI, 'get_ansible_role')
    @patch.object(ForemanAPI, 'post')
    @patch.object(ForemanAPI, 'get')
    def test_assign_ansible_roles_and_override_preserves_requested_order(
            self, mock_get, mock_post, mock_get_ansible_role):
        mock_get.return_value.json.return_value = {"results": []}
        mock_post.return_value = MagicMock()

        mock_get_ansible_role.return_value = [
            {"id": 51, "name": "roles-one"},
            {"id": 52, "name": "roles-two"},
            {"id": 53, "name": "roles-three"},
        ]

        payload = {
            "roles-two": {},
            "roles-one": {},
            "roles-three": {},
        }

        self.api.assign_ansible_roles_and_override("test-host-name", payload)

        first_post_call = mock_post.call_args_list[0]
        self.assertEqual(first_post_call[0][0], "hosts/test-host-name/assign_ansible_roles")
        self.assertEqual(first_post_call[1]['json'], {"ansible_role_ids": [52, 51, 53]})

    @patch.object(ForemanAPI, 'get_ansible_role')
    @patch.object(ForemanAPI, 'post')
    @patch('oc_cdtapi.ForemanAPI.api.logging.warning')
    def test_assign_ansible_roles_logs_unresolved_role(self, mock_warning, mock_post, mock_get_ansible_role):
        # assertLogs is not used here since some sibling test modules disable the root
        # logger at import time with no teardown (logging.getLogger().disabled = True),
        # which silently breaks assertLogs when the whole test suite runs together.
        mock_get_ansible_role.return_value = [
            {"id": 51, "name": "roles-one"},
        ]
        mock_post.return_value = None

        self.api.assign_ansible_roles("test-host-name", ["roles-one", "roles-missing"])

        self.assertTrue(any("roles-missing" in str(call_args) for call_args in mock_warning.call_args_list))

        payload = {
            "ansible_role_ids": [51]
        }
        mock_post.assert_called_once_with(
            "hosts/test-host-name/assign_ansible_roles",
            headers=self.api.headers,
            json=payload
        )

    def test_assign_ansible_roles_and_override_not_dict(self):
        payload = ["roles-one"]

        with self.assertRaises(ForemanAPIError) as e:
            self.api.assign_ansible_roles_and_override("test-host-name", payload)

        self.assertEqual(e.exception.code, 400)
        self.assertIn("Input must be in dict", e.exception.text)

    @patch.object(ForemanAPI, 'get_ansible_role')
    @patch.object(ForemanAPI, 'get')
    def test_assign_ansible_roles_and_override_missing_variable(self, mock_get, mock_get_ansible_role):
        # Mock self.get
        get_variable_one = MagicMock()
        get_variable_one.json.return_value = {
            "results": [
                {"parameter": "version", "id": 1},
                {"parameter": "extras", "id": 2},
                {"parameter": "another-extras", "id": 3},
            ]
        }

        get_variable_two = MagicMock()
        get_variable_two.json.return_value = {
            "results": [
                {"parameter": "version", "id": 4},
                {"parameter": "extras",  "id": 5},
            ]
        }

        mock_get.side_effect = [get_variable_one, get_variable_two]

        mock_get_ansible_role.return_value = [
            {"id": 51, "name": "roles-one", "created_at": "2025-01-27 10:15:38 UTC", "updated_at": "2025-01-27 10:15:38 UTC"},
            {"id": 53, "name": "roles-two", "created_at": "2025-05-14 08:40:53 UTC", "updated_at": "2025-05-14 08:40:53 UTC"}
        ]

        payload = {
            "roles-one": {"version": "1.2.3", "extras": "random"},
            "roles-two": {"version": "1.2.3","another-extras": "random"}
        }

        with self.assertRaises(ForemanAPIError) as e:
            self.api.assign_ansible_roles_and_override("test-host-name", payload)

        mock_get_ansible_role.assert_called_once_with(['roles-one', 'roles-two'])

        expected_get_calls = [
            call(
                "ansible/api/ansible_variables",
                params={"search": "ansible_role=roles-one", "per_page": "all"}
            ),
            call(
                "ansible/api/ansible_variables",
                params={"search": "ansible_role=roles-two", "per_page": "all"}
            )
        ]
        mock_get.assert_has_calls(expected_get_calls, any_order=False)
        self.assertEqual(mock_get.call_count, 2)

        self.assertEqual(e.exception.code, 400)
        self.assertIn("missing variables", e.exception.text)

    def test_check_latest_job_invocation_found(self):
        job = self.api.check_latest_job_invocation("test-ansible-vm")
        self.assertEqual(job["id"], 1000)
        self.assertEqual(job["status"], 0)

    def test_check_latest_job_invocation_none(self):
        job = self.api.check_latest_job_invocation("test-ansible-vm-empty")
        self.assertIsNone(job)

    @patch.object(ForemanAPI, 'get')
    def test_get_all_hosts_reads_every_page(self, mock_get):
        hosts = [{"id": i, "name": "host-%s.example.com" % i} for i in range(250)]
        mock_get.side_effect = [
            _mock_response({"total": 250, "subtotal": 250, "page": 1, "per_page": 100, "results": hosts[0:100]}),
            _mock_response({"total": 250, "subtotal": 250, "page": 2, "per_page": 100, "results": hosts[100:200]}),
            _mock_response({"total": 250, "subtotal": 250, "page": 3, "per_page": 100, "results": hosts[200:250]}),
        ]

        result = self.api.get_all_hosts()

        self.assertEqual(result, hosts)
        self.assertEqual(len({host["id"] for host in result}), 250)
        self.assertEqual(mock_get.call_args_list, [
            call("hosts", params={"page": 1, "per_page": 100}),
            call("hosts", params={"page": 2, "per_page": 100}),
            call("hosts", params={"page": 3, "per_page": 100}),
        ])

    @patch.object(ForemanAPI, 'get')
    def test_get_all_hosts_passes_search_and_thin(self, mock_get):
        mock_get.return_value = _mock_response({"subtotal": 1, "results": [{"id": 1, "name": "host.example.com"}]})

        result = self.api.get_all_hosts(search="name ~ host", thin=True, per_page=50)

        self.assertEqual(result, [{"id": 1, "name": "host.example.com"}])
        mock_get.assert_called_once_with(
            "hosts",
            params={"search": "name ~ host", "thin": "true", "page": 1, "per_page": 50}
        )

    @patch.object(ForemanAPI, 'get')
    def test_get_all_hosts_stops_on_empty_page(self, mock_get):
        hosts = [{"id": i, "name": "host-%s.example.com" % i} for i in range(100)]
        # subtotal promises 300 hosts, but the second page is empty
        mock_get.side_effect = [
            _mock_response({"total": 300, "subtotal": 300, "results": hosts}),
            _mock_response({"total": 300, "subtotal": 300, "results": []}),
            _mock_response({"total": 300, "subtotal": 300, "results": hosts}),
        ]

        result = self.api.get_all_hosts()

        self.assertEqual(result, hosts)
        self.assertEqual(mock_get.call_count, 2)

    @patch.object(ForemanAPI, 'get')
    def test_get_common_parameters(self, mock_get):
        # 'total' counts all global parameters, 'subtotal' only the ones matching the search
        mock_get.side_effect = [
            _mock_response({"total": 40, "subtotal": 3, "search": "name ~ hook", "results": [
                {"id": 1, "name": "hook_disk_digest_enabled", "parameter_type": "boolean", "value": True},
                {"id": 2, "name": "hook_used_disk_space_percentage_warning_lvl", "parameter_type": "integer", "value": 80},
            ]}),
            _mock_response({"total": 40, "subtotal": 3, "search": "name ~ hook", "results": [
                {"id": 3, "name": "hook_smtp_email", "parameter_type": "string", "value": "hooks@example.com"},
            ]}),
        ]

        result = self.api.get_common_parameters(search="name ~ hook")

        self.assertEqual(result, {
            "hook_disk_digest_enabled": True,
            "hook_used_disk_space_percentage_warning_lvl": 80,
            "hook_smtp_email": "hooks@example.com",
        })
        self.assertIs(result["hook_disk_digest_enabled"], True)
        self.assertIsInstance(result["hook_used_disk_space_percentage_warning_lvl"], int)
        self.assertEqual(mock_get.call_args_list, [
            call("common_parameters", params={"search": "name ~ hook", "page": 1, "per_page": 100}),
            call("common_parameters", params={"search": "name ~ hook", "page": 2, "per_page": 100}),
        ])

    @patch.object(ForemanAPI, 'get')
    def test_get_host_enc(self, mock_get):
        enc = {
            "classes": {},
            "environment": "production",
            "parameters": {"owner_email": "owner@example.com", "responsible_person": "jdoe"}
        }
        mock_get.return_value = _mock_response({"data": enc})

        result = self.api.get_host_enc("host.example")

        self.assertEqual(result, enc)
        self.assertIn("parameters", result)
        mock_get.assert_called_once_with("hosts/host.example/enc")

    @patch.object(ForemanAPI, 'get')
    def test_get_host_enc_not_wrapped(self, mock_get):
        enc = {"parameters": {"owner_email": "owner@example.com"}}
        mock_get.return_value = _mock_response(enc)

        result = self.api.get_host_enc("host.example")

        self.assertEqual(result, enc)

    def test_get_host_enc_not_found(self):
        web = MagicMock()
        web.get.return_value = _mock_response(None, status_code=404)
        web.get.return_value.text = '{"error": {"message": "Resource host not found by id \'missing.example\'"}}'
        self.api.web = web

        with self.assertRaises(ForemanAPIError) as err:
            self.api.get_host_enc("missing.example")

        self.assertEqual(err.exception.code, 404)

    @patch.object(ForemanAPI, 'get')
    def test_get_usergroup_members(self, mock_get):
        mock_get.side_effect = [
            _mock_response({"subtotal": 1, "results": [{"id": 7, "name": "Support Infrastructure"}]}),
            _mock_response({
                "id": 7,
                "name": "Support Infrastructure",
                "users": [{"id": 4, "login": "jdoe", "description": None}, {"id": 5, "login": "asmith", "description": None}],
                "usergroups": [{"id": 9, "name": "Nested group"}]
            }),
            _mock_response({"id": 4, "login": "jdoe", "firstname": "John", "lastname": "Doe", "mail": "jdoe@example.com"}),
            _mock_response({"id": 5, "login": "asmith", "firstname": "Anna", "lastname": "Smith", "mail": None}),
        ]

        members = self.api.get_usergroup_members("Support Infrastructure")

        self.assertEqual(members, [
            {"firstname": "John", "lastname": "Doe", "login": "jdoe"},
            {"firstname": "Anna", "lastname": "Smith", "login": "asmith"},
        ])
        # members of the nested group are not read
        self.assertEqual(mock_get.call_args_list, [
            call("usergroups", params={"search": 'name = "Support Infrastructure"'}),
            call("usergroups/7"),
            call("users/4"),
            call("users/5"),
        ])

    @patch.object(ForemanAPI, 'get')
    def test_get_usergroup_members_empty_group(self, mock_get):
        mock_get.side_effect = [
            _mock_response({"subtotal": 1, "results": [{"id": 7, "name": "Support Infrastructure"}]}),
            _mock_response({"id": 7, "name": "Support Infrastructure", "users": []}),
        ]

        members = self.api.get_usergroup_members("Support Infrastructure")

        self.assertEqual(members, [])
        self.assertEqual(mock_get.call_count, 2)

    @patch.object(ForemanAPI, 'get')
    def test_get_usergroup_members_group_not_found(self, mock_get):
        # the search may return groups with a similar name, only an exact match counts
        mock_get.return_value = _mock_response({"subtotal": 1, "results": [{"id": 8, "name": "Support Infrastructure Old"}]})

        with self.assertRaises(ForemanAPIError) as err:
            self.api.get_usergroup_members("Support Infrastructure")

        self.assertEqual(err.exception.code, 404)
        self.assertIn("Support Infrastructure", err.exception.text)
        self.assertEqual(mock_get.call_count, 1)

    def test_read_only_methods_send_only_get(self):
        web = MagicMock()
        # one response that fits every method: a page with one group, its member and an ENC document
        web.get.return_value = _mock_response({
            "subtotal": 1,
            "results": [{"id": 7, "name": "Support Infrastructure"}],
            "users": [{"id": 4, "login": "jdoe"}],
            "login": "jdoe",
            "data": {"parameters": {}}
        })
        self.api.web = web

        self.api.get_all_hosts(search="name ~ host", thin=True)
        self.api.get_common_parameters(search="name ~ hook")
        self.api.get_host_enc("host.example")
        self.api.get_usergroup_members("Support Infrastructure")

        requested_urls = [get_call[0][0] for get_call in web.get.call_args_list]
        self.assertEqual(requested_urls, [
            "https://foreman.example.com/api/hosts",
            "https://foreman.example.com/api/common_parameters",
            "https://foreman.example.com/api/hosts/host.example/enc",
            "https://foreman.example.com/api/usergroups",
            "https://foreman.example.com/api/usergroups/7",
            "https://foreman.example.com/api/users/4",
        ])
        web.post.assert_not_called()
        web.put.assert_not_called()
        web.patch.assert_not_called()
        web.delete.assert_not_called()
        web.request.assert_not_called()