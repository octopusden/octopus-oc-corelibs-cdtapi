import json
import logging
import posixpath
import re
import time
from time import sleep

from oc_cdtapi.API import HttpAPI, HttpAPIError
from collections import namedtuple, defaultdict
from datetime import datetime, timedelta
from packaging import version

class ForemanAPIError(HttpAPIError):
    def __str__(self):
        return self.text


class ForemanAPI(HttpAPI):
    """
    A simple client for Foreman's REST API
    """

    _error = ForemanAPIError
    _env_prefix = "FOREMAN"

    headers = {
        "Accept": "application/json;version=2",
        "Content-Type": "application/json"
    }

    def __init__(self, *args, **kwargs):
        """
        Class initialization, setting the default values for a new host
        """
        super().__init__(*args, **kwargs)
        class_defaults = namedtuple("values", "exp_date location_id hostgroup deploy_on")
        exp_date = self._set_expiration()
        location_id = 5
        hostgroup = 11
        deploy_on = 1
        self.__apiversion = None
        self.defs = class_defaults(exp_date, location_id, hostgroup, deploy_on)
        self.__foreman_version = None
        self.__foreman_version_major = None

    def __set_foreman_versions(self):
        logging.debug('Reached set_foreman_versions')
        response = self.get("status").json()
        self.__foreman_version = response.get("version")
        logging.debug('version = [%s]' % self.__foreman_version)
        self.__apiversion = response.get("api_version")
        logging.debug('api_version = [%s]' % self.__apiversion)

    @property
    def apiversion(self):
        if self.__apiversion:
            return self.__apiversion
        self.__set_foreman_versions()
        return self.__apiversion

    @property
    def foreman_version(self):
        if self.__foreman_version:
            return self.__foreman_version
        self.__set_foreman_versions()
        return self.__foreman_version

    @property
    def foreman_version_major(self):
        if self.__foreman_version_major:
            return self.__foreman_version_major
        self.__foreman_version_major = version.parse(self.foreman_version).major
        return self.__foreman_version_major

    def re(self, req):
        if not req.startswith(("foreman_puppet", "ansible")):
            return posixpath.join(self.root, "api", req)
        else:
            return posixpath.join(self.root, req)

    def get_host_by_owner(self, owner):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_host_by_owner')
        logging.debug('owner = [%s]' % owner)
        if self.apiversion == 1:
            logging.error('Not supported in v1, returning None')
            return None
        elif self.apiversion == 2:
            logging.debug('Passing to get_host_by_owner_v2')
            return self.get_host_by_owner_v2(owner)

    def get_host_by_owner_v2(self, owner):
        logging.debug('Reached get_host_by_owner_v2')
        logging.debug('owner = [%s]' % owner)
        params = {
            'search': f'owner={owner}',
            'per_page': 'all'
        }
        response = self.get('hosts', params=params).json()
        results = response.get('results')
        return results

    def get_environment(self, env_name):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_environment')
        logging.debug('env_name = [%s]' % env_name)
        if self.apiversion == 1:
            logging.error('Not supported in v1, returning None')
            return None
        elif self.apiversion == 2:
            logging.debug('Passing to get_environment_v2')
            return self.get_environment_v2(env_name)

    def get_environment_v2(self, env_name):
        """
        returns environment id for env_name
        """
        logging.debug('Reached get_environment_v2')
        logging.debug('env_name = [%s]' % env_name)
        params = {'search': 'name=%s' % env_name}
        response = self.get('environments', params=params).json()
        results = response.get('results')
        for result in results:
            if result.get('name') != env_name:
                continue

            env_id = result.get('id')
            logging.debug('Found environment [%s]' % env_id)
            return env_id

        logging.error('Could not find environment for [%s], returning None' % env_name)
        return None

    def get_owner(self, user_login):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_owner')
        if self.apiversion == 1:
            logging.debug('Passing to get_owner_v1')
            return self.get_owner_v1(user_login)
        elif self.apiversion == 2:
            logging.debug('Passing to get_owner_v2')
            return self.get_owner_v2(user_login)

    def get_owner_v1(self, user_login):
        """
        Looks for user id in the Foreman DB
        """
        logging.debug('Reached get_owner_v1')
        try:
            params = {'search': 'login=%s' % user_login}
            response = self.get('users', params=params)
        except ForemanAPIError as err:
            raise (err)

        data = json.loads(response.text)

        try:
            user_id = data["results"][0]["id"]
        except IndexError:
            user_id = None

        return user_id

    def get_owner_v2(self, user_login):
        """
        did not change since v1
        """
        logging.debug('Reached get_owner_v2')
        logging.debug('Passing to get_owner_v1')
        return self.get_owner_v1(user_login)

    def get_usergroup_id(self, group_name):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_usergroup_id')
        if self.apiversion == 1:
            logging.debug('Passing to get_usergroup_id_v1')
            return self.get_usergroup_id_v1(group_name)
        if self.apiversion == 2:
            logging.debug('Passing to get_usergroup_id_v2')
            return self.get_usergroup_id_v2(group_name)

    def get_usergroup_id_v1(self, group_name):
        """
        Looks for usergroup id in the Foreman DB
        """
        logging.debug('Reached get_usergroup_id_v1')
        if re.search("\s", group_name):
            group_name = "%22{}%22".format(re.sub("\s", "%20", group_name))

        # removed catching error since it is raised again
        params = {'search': 'name=%s' % group_name}
        response = self.get('usergroups', params=params)

        data = response.json()

        try:
            group_id = data["results"][0]["id"]
        except IndexError:
            group_id = None

        return group_id

    def get_usergroup_id_v2(self, group_name):
        """
        Looks for usergroup id in the Foreman DB
        """
        logging.debug('Reached get_usergroup_id_v2')
        logging.debug('Passing to get_usergroup_id_v1')
        return self.get_usergroup_id_v1(group_name)

    def _set_expiration(self):
        """
        A private method which sets the default expiration date (3 months from the current date)
        """
        logging.debug('Reached _set_expiration')
        return str((datetime.now() + timedelta(days=90)).strftime('%d/%m/%Y'))

    def create_host(self, hostname=None, cores=1, memory=4096, disk=50, owner_id=None,
                    exp_date=None, location_id=None, hostgroup=None,
                    deploy_on=None, custom_json=None):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached create_host')
        logging.debug('hostname = [%s]' % hostname)
        logging.debug('cores = [%s]' % cores)
        logging.debug('memory = [%s]' % memory)

        if self.apiversion == 1:
            logging.debug('Passing to create_host_v1')
            self.create_host_v1(hostname, cores, memory, disk, owner_id,
                                exp_date, location_id, hostgroup,
                                deploy_on, custom_json)
        elif self.apiversion == 2:
            logging.debug('Passing to create_host_v2')
            # This is wierd horror: caller provides 'task' as 'hostname' argument!
            self.create_host_v2(hostname, custom_json)

    def create_host_v1(self, hostname, cores, memory, disk, owner_id,
                       exp_date, location_id, hostgroup,
                       deploy_on, custom_json):
        """
        Creates a host using the default parameters or the ones from an external json
        note that create_vm in engine actually sends db_task instead of hostname and custom_json,
        other parms are ignored
        """
        logging.debug('Reached create_host_v1')
        logging.debug('hostname = [%s]' % hostname)

        if not exp_date:
            exp_date = self._set_expiration()
        if not location_id:
            location_id = self.defs.location_id
        if not hostgroup:
            hostgroup = self.defs.hostgroup
        if not deploy_on:
            deploy_on = self.defs.deploy_on

        default_params = {
            "name": hostname,
            "compute_attributes": {
                "start": "1",
                "cpus": cores,
                "memory_mb": memory,
                "volumes_attributes": {
                    0: {
                        "size_gb": disk
                    },
                },
            },
            "location_id": location_id,
            "hostgroup_id": hostgroup,
            "compute_resource_id": deploy_on,
            "is_owned_by": owner_id,
            "build": "true",
            "expired_on": exp_date
        }

        if custom_json:
            custom = json.loads(custom_json)
            default_params.update(custom)

        if not default_params["is_owned_by"]:
            raise ForemanAPIError(code=400, text="The owner id is not specified")

        if not default_params["name"]:
            raise ForemanAPIError(code=400, text="The hostname is not specified")

        logging.debug("ForemanAPI is about to send the following payload:")
        logging.debug(default_params)
        request = self.post("hosts", headers=self.headers, json=default_params)

    def create_host_v2(self, task, custom_json):

        logging.debug('Reached create_host_v2')
        logging.debug('task = [%s]' % task)
        hostname = task['task_content']['resources']['name']
        logging.debug('hostname = [%s]' % hostname)
        cores = 1
        memory = 4096
        disk = 50
        owner_id = None

        exp_date = self._set_expiration()
        location_id = self.defs.location_id
        hostgroup = self.defs.hostgroup
        deploy_on = self.defs.deploy_on
        domain_id = self.get_domain_id(hostname)
        arch_id = self.get_architecture_id('x86_64')
        os_id = self.get_os_id('CentOS Linux 7.9.2009')
        ptable_id = self.get_ptable_id(os_id, 'CDT LVM')

        default_params = {
            "name": hostname,
            "compute_attributes": {
                "start": "1",
                "cpus": cores,
                "memory_mb": memory,
                "volumes_attributes": {
                    0: {
                        "size_gb": disk
                    },
                },
            },
            "location_id": location_id,
            "hostgroup_id": hostgroup,
            "compute_resource_id": deploy_on,
            "is_owned_by": owner_id,
            "build": "true",
            "expired_on": exp_date,
            "domain_id": domain_id,
            "architecture_id": arch_id,
            "operatingsystem_id": os_id,
            "ptable_id": ptable_id
        }

        if custom_json:
            custom = json.loads(custom_json)
            default_params.update(custom)

        if not default_params["is_owned_by"]:
            raise ForemanAPIError(code=400, text="The owner id is not specified")

        if not default_params["name"]:
            raise ForemanAPIError(code=400, text="The hostname is not specified")

        if not default_params.get('hostgroup_id'):
            hostgroup = self.get_hostgroup_id('stands')
            logging.debug('houstgroup_id is not set, setting default [%s]' % hostgroup)
            default_params['hostgroup_id'] = hostgroup

        if not default_params.get('environment_id'):
            env_id = self.get_environment('production')
            logging.debug('environment_id is not set, setting default [%s]' % env_id)
            default_params['environment_id'] = env_id

        logging.debug("ForemanAPI is about to send the following payload:")
        logging.debug(default_params)
        request = self.post("hosts", headers=self.headers, json=default_params)

    def get_architecture_id(self, arch_name):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_architecture_id')
        logging.debug('arch_name = [%s]')
        if self.apiversion == 1:
            # message appneded since different logging level on above and here
            logging.error('Get_Architecture_ID is not supported in v1, returning None')
            return None
        elif self.apiversion == 2:
            logging.debug('Passing to get_architecture_id_v2')
            return self.get_architecture_id_v2(arch_name)

    def get_architecture_id_v2(self, arch_name):
        """
        returns architecture id
        """
        logging.debug('Reached get_architecture_id_v2')
        logging.debug('arch_name = [%s]' % arch_name)
        params = {'search': 'name=%s' % arch_name}
        response = self.get('architectures', params=params).json()
        logging.debug('Received response: %s')
        logging.debug(response)
        results = response.get('results')

        for result in results:
            if result.get('name') != arch_name:
                continue

            arch_id = result.get('id')
            logging.debug('Found architecture, id = [%s]' % id)
            return arch_id

        logging.error('No architecture found, returning None')
        return None

    def get_domain_id(self, hostname):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_domain_id')

        if self.apiversion == 1:
            logging.error('Not supported in v1, returning None')
            return None
        elif self.apiversion == 2:
            logging.debug('Passing to get_domain_id_v2')
            return self.get_domain_id_v2(hostname)

    def get_domain_id_v2(self, hostname):
        """
        Returns domain id if found
        """
        logging.debug('Reached get_domain_id_v2')
        logging.debug('hostname = [%s]' % hostname)
        domain = '.'.join(hostname.split('.')[1:])
        response = self.get('domains')
        j = response.json()
        domains = j['results']
        logging.debug('Searching domain [%s]' % domain)
        logging.debug('Domains list:')
        logging.debug(domains)

        for d in domains:
            if d.get('name') == domain:
                return d.get('id')

        logging.error('Cannot find domain for host [%s]' % hostname)
        return None

    def get_host_info(self, hostname):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_host_info')
        if self.apiversion == 1:
            logging.debug('Passing to get_host_info_v1')
            return self.get_host_info_v1(hostname)
        elif self.apiversion == 2:
            logging.debug('Passing to get_host_info_v2')
            return self.get_host_info_v2(hostname)

    def get_host_info_v1(self, hostname):
        """
        Gathers all information about the host and returns it as a json
        """
        logging.debug('Reached get_host_info_v1')
        logging.debug('hostname = [%s]' % hostname)
        response = self.get(posixpath.join("hosts", hostname))
        return response.json()

    def get_host_info_v2(self, hostname):
        logging.debug('Reached get_host_info_v2')
        logging.debug('hostname = [%s]' % hostname)
        logging.debug('passing to get_host_info_v1')
        return self.get_host_info_v1(hostname)

    def get_ptable_id(self, os_id, ptable_name):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_ptable_id')
        if self.apiversion == 1:
            logging.error('Get_Ptable_Id is not supported in v1, returning None')
            return None
        elif self.apiversion == 2:
            logging.debug('Passing to get_ptable_id_v2')
            return self.get_ptable_id_v2(os_id, ptable_name)

    def get_ptable_id_v2(self, os_id, ptable_name):
        """
        returns partition table id
        """
        logging.debug('Reached get_ptable_id_v2')
        logging.debug('os_id = [%s]' % os_id)
        logging.debug('ptable_name = [%s]' % ptable_name)
        response = self.get(posixpath.join('operatingsystems', str(os_id), 'ptables')).json()
        logging.debug('response is:')
        logging.debug(response)
        results = response.get('results')
        for result in results:
            if result.get('name') != ptable_name:
                continue

            ptable_id = result.get('id')
            logging.debug('Found ptable id = [%s]' % ptable_id)
            return ptable_id

        logging.error('No ptable found, returning None')
        return None

    def update_host(self, hostname, payload):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached update_host')
        if self.apiversion == 1:
            logging.debug('Passing to update_host_v1')
            self.update_host_v1(hostname, payload)
        elif self.apiversion == 2:
            logging.debug('Passing to update_host_v2')
            self.update_host_v2(hostname, payload)

    def update_host_v1(self, hostname, payload):
        """
        Updates the host using the payload
        """
        logging.debug('Reached update_host_v1')
        logging.debug(f"Payload: {payload}")
        request = self.put(posixpath.join("hosts", hostname), headers=self.headers, json=payload)

    def update_host_v2(self, hostname, payload):
        """
        Updates the host using the payload
        """
        logging.debug('Reached update_host_v2')
        logging.debug('Passing to update_host_v1')
        self.update_host_v1(hostname, payload)

    def delete_host(self, hostname):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached delete_host')
        if self.apiversion == 1:
            logging.debug('Passing to delete_host_v1')
            self.delete_host_v1(hostname)
        elif self.apiversion == 2:
            logging.debug('Passing to delete_host_v2')
            self.delete_host_v2(hostname)

    def delete_host_v1(self, hostname):
        """
        Deletes the specified host
        """
        logging.debug('Reached delete_host_v1')
        request = self.delete(posixpath.join("hosts", hostname), headers=self.headers)

    def delete_host_v2(self, hostname):
        """
        Deletes the specified host
        """
        logging.debug('Reached delete_host_v2')
        logging.debug('Passing to delete_host_v1')
        self.delete_host_v1(hostname)

    def puppet_class_info(self, classname):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached puppet_class_info')
        if self.apiversion == 1:
            logging.debug('Passing to puppet_class_info_v1')
            return self.puppet_class_info_v1(classname)
        elif self.apiversion == 2:
            if self.foreman_version_major == 2:
                logging.debug('Passing to puppet_class_info_v1')
                return self.puppet_class_info_v1(classname)
            else:
                logging.debug('Passing to puppet_class_info_v2')
                return self.puppet_class_info_v2(classname)

    def puppet_class_info_v1(self, classname):
        """
        Returns puppet class info
        """
        logging.debug('Reached puppet_class_info_v1')
        response = self.get(posixpath.join("puppetclasses", classname), headers=self.headers)
        return response.json()

    def puppet_class_info_v2(self, classname):
        """
        Returns puppet class info
        """
        logging.debug('Reached puppet_class_info_v2')
        response = self.get(posixpath.join("foreman_puppet", "api", "puppetclasses", classname), headers=self.headers)
        return response.json()

    def smart_class_info(self, scid):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached smart_class_info')

        if self.apiversion == 1:
            logging.debug('Passing to smart_class_info_v1')
            return self.smart_class_info_v1(scid)
        if self.apiversion == 2:
            logging.debug('Passing to smart_class_info_v2')
            return self.smart_class_info_v2(scid)

    def smart_class_info_v1(self, scid):
        """
        Returns smart class info
        """
        logging.debug('Reached smart_class_info_v1')
        response = self.get(posixpath.join("smart_class_parameters", str(scid)), headers=self.headers)
        return response.json()

    def smart_class_info_v2(self, scid):
        """
        Returns smart class info
        """
        logging.debug('Reached smart_class_info_v2')
        logging.debug('Passing to smart_class_info_v1')
        return self.smart_class_info_v1(scid)

    def override_smart_class(self, scid, params):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached mverride_smart_class')
        if self.apiversion == 1:
            logging.debug('Passing to override_smart_class_v1')
            self.override_smart_class_v1(scid, params)
        elif self.apiversion == 2:
            logging.debug('Passing to override_smart_class_v2')
            self.override_smart_class_v1(scid, params)

    def override_smart_class_v1(self, scid, params):
        """
        Overrides smart class parameters
        """
        logging.debug('Reached override_smart_class_v1')
        request = self.post(posixpath.join("smart_class_parameters", str(scid),
                                           "override_values"), headers=self.headers, data=params)

    def override_smart_class_v2(self, scid, params):
        """
        Overrides smart class parameters
        """
        logging.debug('Reached override_smart_class_v2')
        logging.debug('Passing to override_smart_class_v1')
        self.override_smart_class_v1(scid, params)

    def get_hostgroup_puppetclasses(self, hostgroup_id):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_hostgroup_puppetclasses')
        if self.apiversion == 1:
            logging.debug('Passing to get_hostgroup_puppetclasses_v1')
            return self.get_hostgroup_puppetclasses_v1(hostgroup_id)
        elif self.apiversion == 2:
            if self.foreman_version_major == 2:
                logging.debug('Passing to get_hostgroup_puppetclasses_v1')
                return self.get_hostgroup_puppetclasses_v1(hostgroup_id)
            else:
                logging.debug('Passing to get_hostgroup_puppetclasses_v2')
                return self.get_hostgroup_puppetclasses_v2(hostgroup_id)

    def get_hostgroup_puppetclasses_v1(self, hostgroup_id):
        """
        Returns info about all hostgroup's puppetclasses
        """
        logging.debug('Reached get_hostgroup_puppetclasses_v1')
        response = self.get(posixpath.join("hostgroups", str(hostgroup_id), "puppetclasses"), headers=self.headers)
        return response.json()

    def get_hostgroup_puppetclasses_v2(self, hostgroup_id):
        """
        Returns info about all hostgroup's puppetclasses
        """
        logging.debug('Reached get_hostgroup_puppetclasses_v2')
        response = self.get(posixpath.join('foreman_puppet', 'api', 'hostgroups', str(hostgroup_id), 'puppetclasses'))
        return response.json()

    def add_puppet_class_to_host(self, hostname, params):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached add_puppet_class_to_host')
        if self.apiversion == 1:
            logging.debug('Passing to add_puppet_class_to_host_v1')
            self.add_puppet_class_to_host_v1(hostname, params)
        if self.apiversion == 2:
            if self.foreman_version_major == 2:
                logging.debug('Passing to add_puppet_class_to_host_v1')
                self.add_puppet_class_to_host_v1(hostname, params)
            else:
                logging.debug('Passing to add_puppet_class_to_host_v2')
                self.add_puppet_class_to_host_v2(hostname, params)

    def add_puppet_class_to_host_v1(self, hostname, params):
        """
        Adds the required puppet class to the host
        """
        logging.debug('Reached add_puppet_class_to_host_v1')
        request = self.post(posixpath.join("hosts", hostname, "puppetclass_ids"), headers=self.headers, data=params)

    def add_puppet_class_to_host_v2(self, hostname, params):
        """
        Adds the required puppet class to the host
        """
        logging.debug('Reached add_puppet_class_to_host_v2')
        logging.debug('Params to be sent: %s' % params)
        response = self.post(posixpath.join('foreman_puppet', 'api', 'hosts', hostname, 'puppetclass_ids'),
                             headers=self.headers, data=params)

    def get_subnets(self):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_subnets')
        if self.apiversion == 1:
            logging.debug('Passing to get_subnets_v1')
            return self.get_subnets_v1()
        elif self.apiversion == 2:
            logging.debug('Passing to get_subnets_v2')
            return self.get_subnets_v2()

    def get_subnets_v1(self):
        """
        Returns all available subnets
        """
        logging.debug('Reached get_subnets_v1')
        subnets_count = self.get("subnets", headers=self.headers).json()["total"]
        response = self.get("subnets?per_page={}".format(subnets_count), headers=self.headers)
        return response.json()

    def get_subnets_v2(self):
        """
        Return all available subnets
        """
        logging.debug('Reached get_subnets_v2')
        logging.debug('Passing to get_subnets_v1')
        return self.get_subnets_v1()

    def get_host_reports(self, hostname, last=False):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_host_reports')
        if self.apiversion == 1:
            logging.debug('Passing to get_host_reports_v1')
            return self.get_host_reports_v1(hostname, last)
        elif self.apiversion == 2:
            logging.debug('Passing to get_host_reports_v2')
            return self.get_host_reports_v2(hostname, last)

    def get_host_reports_v1(self, hostname, last):
        """
        Returns all reports (or only the last one) for the host
        """
        _rq = posixpath.join("hosts", hostname, "config_reports")

        if last:
            _rq = posixpath.join(_rq, "last")

        response = self.get(_rq, headers=self.headers)

        return response.json()

    def get_host_reports_v2(self, hostname, last):
        """
        Returns all reports (or only the last one) for the host
        """
        logging.debug('Reached get_host_reports_v2')
        logging.debug('hostname = [%s]' % hostname)
        logging.debug('last = [%s]' % last)
        if not last:
            params = {'search': 'host=%s' % hostname}
            response = self.get('config_reports', params=params).json()
            logging.debug('Received response:')
            logging.debug(response)
        else:
            host_id = self.get_host_info(hostname).get('id')
            logging.debug('host_id = [%s]' % host_id)
            response = self.get(posixpath.join('hosts', str(host_id), "config_reports", "last")).json()
            logging.debug('Received response:')
            logging.debug(response)
        return response

    def is_host_powered_on(self, hostname):
        """
        Returns true if host is powered on
        """
        logging.debug('Reached is_host_powered_on')
        response = self.get(posixpath.join("hosts", hostname, "power")).json()
        return response['state'] == 'on'

    def host_power(self, hostname, action):
        """
        wrapper for api v1/v2
        NB currently (2023-02-08) host power is managed via vsphere api
        """
        logging.debug('Reached host_power')
        if self.apiversion == 1:
            logging.debug('Passing to host_power_v1')
            self.host_power_v1(hostname, action)
        elif self.apiversion == 2:
            logging.debug('Passing to host_power_v2')
            self.host_power_v2(hostname, action)

    def host_power_v1(self, hostname, action):
        """
        Turns on/off power on the host
        """
        logging.debug('Reached host_power_v1')
        actions = ["start", "stop"]

        if action not in actions:
            raise ForemanAPIError(code=500, text="Incorrect power action was provided")

        params = json.dumps({"power_action": action})
        request = self.put(posixpath.join("hosts", hostname, "power"), headers=self.headers, data=params)

    def host_power_v2(self, hostname, action):
        """
        Turns on/off power on the host
        """
        logging.debug('Reached host_power_v2')
        actions = ["on", "off"]
        if action not in actions:
            raise ForemanAPIError(code=500, text="Incorrect power action was provided")
        params = json.dumps({"power_action": action})
        request = self.put(posixpath.join('hosts', hostname, "power"), headers=self.headers, data=params)
        if not request.status_code == 200:
            logging.error('Server returned an error [%s] [%s]' % (request.status_code, request.text))

    def get_report(self, id):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_report')
        if self.apiversion == 1:
            logging.debug('Passing to get_report_v1')
            return self.get_report_v1(id)
        elif self.apiversion == 2:
            logging.debug('Passing to get_report_v2')
            return self.get_report_v2(id)

    def get_report_v1(self, id):
        """
        Returns a foreman report with specified id
        :param id: int, id of the required report
        :return: response in json format
        """
        response = self.get(posixpath.join("config_reports", str(id)), headers=self.headers)
        return response.json()

    def get_report_v2(self, id):
        """
        Returns a foreman report with specified id
        :param id: int, id of the required report
        :return: response in json format
        """
        logging.debug('Reached get_report_v2')
        logging.debug('Passing to get_report_v1')
        return self.get_report_v1(id)

    def get_hostgroup_id(self, hostgroup_name):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_hostgroup_id')
        if self.apiversion == 1:
            logging.debug('Passing to get_hostgroup_id_v1')
            return self.get_hostgroup_id_v1(hostgroup_name)
        elif self.apiversion == 2:
            logging.debug('Passing to get_hostgroup_id_v2')
            return self.get_hostgroup_id_v2(hostgroup_name)

    def get_hostgroup_id_v1(self, hostgroup_name):
        """
        Returns id of the required hostgroup
        :param hostgroup_name: str
        :return: int
        """
        logging.debug('Reached get_hostgroup_id_v1')
        hostgroups = self.get("hostgroups", headers=self.headers).json()["results"]

        for hostgroup in hostgroups:
            if hostgroup.get("name") == hostgroup_name:
                return hostgroup.get('id')

        logging.debug("Hostgroup [%s] not found, returning None" % hostgroup_name)
        return None

    def get_hostgroup_id_v2(self, hostgroup_name):
        """
        Returns id of the required hostgroup
        :param hostgroup_name: str
        :return: int
        """
        logging.debug('Reached get_hostgroup_id_v2')
        logging.debug('Passing to get_hostgroup_id_v1')
        return self.get_hostgroup_id_v1(hostgroup_name)

    def get_organization_id(self, organization_name):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached get_organization_id')
        if self.apiversion == 1:
            logging.debug('Passing to get_organization_id_v1')
            return self.get_organization_id_v1(organization_name)
        elif self.apiversion == 2:
            logging.debug('Passing to get_organization_id_v2')
            return self.get_organization_id_v2(organization_name)

    def get_organization_id_v1(self, organization_name):
        """
        Returns id of the required organization
        :param organization_name: str
        :return: int
        """
        logging.debug('Reached get_organization_id_v1')
        organization_id = None
        organizations_count = self.get("organizations", headers=self.headers).json()["total"]
        organizations = self.get("organizations?per_page={}".format(
            organizations_count), headers=self.headers).json()["results"]

        try:
            organization_id = next(organization["id"]
                                   for organization in organizations if organization["name"] == organization_name)
            return organization_id
        except StopIteration:
            return None

    def get_organization_id_v2(self, organization_name):
        """
        Returns id of the required organization
        :param organization_name: str
        :return: int
        """
        logging.debug('Reached get_organization_id_v2')
        logging.debug('Passing to get_organization_id_v1')
        return self.get_organization_id_v1(organization_name)

    def get_os_id(self, os_name):
        """
        Wrapper for api v1/v2
        """
        logging.debug('Reached get_os_id')
        logging.debug('os_name = [%s]')
        if self.apiversion == 1:
            logging.error('Not supported in v1, returning None')
            return None
        elif self.apiversion == 2:
            logging.debug('Passing to get_os_id_v2')
            return self.get_os_id_v2(os_name)

    def get_os_id_v2(self, os_name):
        """
        returns operating system id
        """
        logging.debug('Reached get_os_id_v2')
        logging.debug('os_name = [%s]' % os_name)
        params = {'search': 'name=%s' % os_name}
        response = self.get('operatingsystems', params=params).json()
        logging.debug('response is:')
        logging.debug(response)
        results = response.get('results')
        for result in results:
            if result.get('description') != os_name:
                continue

            os_id = result.get('id')
            logging.debug('Found os, id = [%s]' % os_id)
            return os_id

        logging.error('OS not found, returning None')
        return None

    def set_host_expiry(self, hostname, expiry):
        """
        wrapper for api v1/v2
        """
        logging.debug('Reached set_host_expiry')
        if self.apiversion == 1:
            logging.debug('Passing to set_host_expiry_v1')
            self.set_host_expiry_v1(hostname, expiry)
        elif self.apiversion == 2:
            logging.debug('Passing to set_host_expiry_v2')
            self.set_host_expiry_v2(hostname, expiry)

    def set_host_expiry_v1(self, hostname, expiry):
        """
        Attempts to set host expiry date
        :param hostname: full hostname
        :param expiry: expiry date in format yyyy-mm-dd
        """
        logging.debug('Reached set_host_expiry_v1')
        pl = {}
        pl['host'] = {}
        pl['host']['expired_on'] = expiry
        self.update_host(hostname, pl)

    def set_host_expiry_v2(self, hostname, expiry):
        """
        Attempts to set host expiry date
        :param hostname: full hostname
        :param expiry: expiry date in format yyyy-mm-dd
        """
        logging.debug('Reached set_host_expiry_v2')
        logging.debug('Passing to set_host_expiry_v1')
        self.set_host_expiry_v1(hostname, expiry)

    def get_image_uuid(self, os_name, image_name):
        """
        wrapper api v1/v2
        """
        logging.debug('Reached get_image_uuid')
        if self.apiversion == 1:
            logging.debug('Passing to get_image_uuid_v1')
            return self.get_image_uuid_v1(os_name, image_name)
        elif self.apiversion == 2:
            logging.debug('Passing to get_image_uuid_v2')
            return self.get_image_uuid_v2(os_name, image_name)

    def get_image_uuid_v1(self, os_name, image_name):
        """
        Returns OS image uuid
        :param os_name: str
        :param image_name: str
        :return: str
        """
        logging.debug('Reached get_image_uuid_v1')
        os_list = self.get("operatingsystems", headers=self.headers).json()["results"]
        try:
            os_id = next(os["id"] for os in os_list if os["description"] == os_name)
            images_list = self.get(posixpath.join("operatingsystems", str(os_id), "images")).json()["results"]
            image_uuid = next(image["uuid"] for image in images_list if image["name"] == image_name)
            return image_uuid
        except StopIteration:
            return None

    def get_image_uuid_v2(self, os_name, image_name):
        """
        Returns OS image uuid
        :param os_name: str
        :param image_name: str
        :return: str
        """
        logging.debug('Reached get_image_uuid_v2')
        logging.debug('Passing to get_image_uuid_v1')
        return self.get_image_uuid_v1(os_name, image_name)

    def get_flavor_id(self, compute_resource_id, flavor_name):
        """
        wrapper api v1/v2
        """
        logging.debug('Reached get_flavor_id')
        if self.apiversion == 1:
            logging.debug('Passing to get_flavor_id_v1')
            return self.get_flavor_id_v1(compute_resource_id, flavor_name)
        elif self.apiversion == 2:
            logging.debug('Passing to get_flavor_id_v2')
            return self.get_flavor_id_v2(compute_resource_id, flavor_name)

    def get_flavor_id_v1(self, compute_resource_id, flavor_name):
        """
        :param compute_resource_id: int
        :param flavor_name: str
        :return: int
        """
        logging.debug('Reached get_flavor_id_v1')
        flavors_list = self.get(posixpath.join("compute_resources", str(compute_resource_id),
                                               "available_flavors")).json()["results"]

        try:
            flavor_id = next(flavor["id"] for flavor in flavors_list if flavor["name"] == flavor_name)
            return flavor_id
        except StopIteration:
            return None

    def get_flavor_id_v2(self, compute_resource_id, flavor_name):
        """
        :param compute_resource_id: int
        :param flavor_name: str
        :return: int
        """
        logging.debug('Reached get_flavor_id_v2')
        logging.debug('Passing to get_flavor_id_v1')
        return self.get_flavor_id_v1(compute_resource_id, flavor_name)

    def get_tenant_id(self, compute_resource_id):
        """
        wrapper api v1/v2
        """
        logging.debug('Reached get_tenant_id')
        if self.apiversion == 1:
            logging.debug('Passing to get_tenant_id_v1')
            return self.get_tenant_id_v1(compute_resource_id)
        elif self.apiversion == 2:
            logging.debug('Passing to get_tenant_id_v2')
            return self.get_tenant_id_v2(compute_resource_id)

    def get_tenant_id_v1(self, compute_resource_id):
        """
        :param compute_resource_id: int
        :return: str
        """
        logging.debug('Reached get_tenant_id_v1')
        compute_resource_info = self.get(posixpath.join("compute_resources", str(compute_resource_id))).json()

        try:
            tenant_id = compute_resource_info["compute_attributes"][0]["attributes"]["tenant_id"]
            return tenant_id
        except KeyError:
            return None

    def get_tenant_id_v2(self, compute_resource_id):
        """
        :param compute_resource_id: int
        :return: str
        """
        logging.debug('Reached get_tenant_id_v2')
        logging.debug('Passing to get_tenant_id_v1')
        return self.get_tenant_id_v1(compute_resource_id)

    def get_hosts_uuids(self, hostnames):
        """
        wrapper api v1/v2
        """
        logging.debug('Reached get_hosts_uuids')
        if self.apiversion == 1:
            logging.debug('Passing to get_hosts_uuids_v1')
            return self.get_hosts_uuids_v1(hostnames)
        elif self.apiversion == 2:
            logging.debug('Passing to get_hosts_uuids_v2')
            return self.get_hosts_uuids_v2(hostnames)

    def get_hosts_uuids_v1(self, hostnames):
        """
        :param hostnames: list
        :return: dict
        """
        logging.debug('Reached get_hosts_uuids_v1')
        hosts_total_qty = self.get("hosts", params={"per_page": 1}).json()["total"]
        hostnames_uuids = {host["name"]: host["uuid"]
                           for host in self.get("hosts", params={"per_page": hosts_total_qty}).json()["results"]}
        uuids = {hostname: uuid for hostname, uuid in hostnames_uuids.items() if hostname in hostnames}
        return uuids

    def get_hosts_uuids_v2(self, hostnames):
        """
        :param hostnames: list
        :return: dict
        """
        logging.debug('Reached get_hosts_uuids_v2')
        logging.debug('Passing to get_hosts_uuids_v1')
        return self.get_hosts_uuids_v1(hostnames)

    def get_host_uuid(self, hostname):
        """
        wrapper api v1/v2
        """
        logging.debug('Reached get_host_uuid')
        if self.apiversion == 1:
            logging.debug('Passing to get_host_uuid_v1')
            return self.get_host_uuid_v1(hostname)
        elif self.apiversion == 2:
            logging.debug('Passing to get_host_uuid_v2')
            return self.get_host_uuid_v2(hostname)

    def get_host_uuid_v1(self, hostname):
        """
        :param hostname: str
        :return: str
        """
        logging.debug('Reached get_host_uuid_v1')
        try:
            return self.get(posixpath.join("hosts", hostname)).json()["uuid"]
        except KeyError:
            return None

    def get_host_uuid_v2(self, hostname):
        """
        :param hostname: str
        :return: str
        """
        logging.debug('Reached get_host_uuid_v2')
        logging.debug('Passing to get_host_uuid_v1')
        return self.get_host_uuid_v1(hostname)

    def get_host_disk_size(self, hostname):
        """
        :param hostname: str
        :return: int
        """
        logging.debug('Reached get_host_disk_size')
        response = self.get(posixpath.join("hosts", hostname, "vm_compute_attributes"))
        data = response.json()
        try:
            volumes = data.get("volumes_attributes", {})
            volume = volumes.get("0") or volumes.get(0)
            if volume and "size_gb" in volume:
                return int(volume["size_gb"])
            logging.error('Could not find size_gb in vm_compute_attributes for [%s]' % hostname)
            return None
        except (KeyError, ValueError, TypeError) as e:
            logging.error('Error parsing disk size for [%s]: %s' % (hostname, e))
            return None

    def get_host_memory_mb(self, hostname):
        """
        :param hostname: str
        :return: int
        """
        logging.debug('Reached get_host_memory_mb')
        response = self.get(posixpath.join("hosts", hostname, "vm_compute_attributes"))
        data = response.json()

        try:
            memory_mb = data.get("memory_mb")
            if memory_mb is not None:
                return int(memory_mb)
            logging.error('Could not find memory_mb in vm_compute_attributes for [%s]' % hostname)
            return None
        except (ValueError, TypeError) as e:
            logging.error('Error parsing memory_mb for [%s]: %s' % (hostname, e))
            return None

    def get_all_users(self):
        """
        :return: list
        """
        users_qty = self.get("users", params={"per_page": 1}).json()["total"]
        users = [{"firstname": user["firstname"], "lastname": user["lastname"], "login": user["login"]}
                 for user in self.get("users", params={"per_page": users_qty}).json()["results"]]
        return users

    def get_all_usergroups(self):
        """
        :return: list
        """
        groups_qty = self.get("usergroups", params={"per_page": 1}).json()["total"]
        groups = [group["name"] for group in self.get("usergroups", params={"per_page": groups_qty}).json()["results"]]
        return groups

    def set_host_owner(self, hostname, owner):
        """
        Change host owner
        :param hostname: str
        :param owner: str
        """
        logging.debug('Reached set_host_owner')
        owner_id = self.get_owner(owner)
        owner_type = 'User'

        if not owner_id:
            owner_id = self.get_usergroup_id(owner)
            owner_type = 'Usergroup'

        if not owner_id:
            raise ForemanAPIError(code=404, text=f"The owner [{owner}] is not found")

        self.update_host(hostname, {"host": {"owner_id": owner_id, "owner_type": owner_type}})

    def set_host_owner_id(self, hostname, owner_id):
        """
        Change host owner_id
        :param hostname: str
        :param owner_id: str
        """
        logging.debug('Reached set_host_owner_id')
        pl = {}
        pl['host'] = {}
        pl['host']['owner_id'] = owner_id
        self.update_host(hostname, pl)

    def set_backup_policy(self, hostname, backup_policy):
        """
        Change backup policy
        :param hostname: str
        :param backup_policy: str
        """
        logging.debug('Reached set_backup_policy')
        payload = {
            "parameter": {
                "value": backup_policy
            }
        }
        self.update_host(hostname=hostname, payload=payload)

    def get_job_template_id(self, template_name):
        """
        Get template ID by name. Cache results to avoid repeated API calls.
        :param template_name: str
        :return template_id: int
        """
        logging.debug('Reached get_job_template_id')
        if not hasattr(self, '_template_cache'):
            self._template_cache = {}

        if template_name in self._template_cache:
            return self._template_cache[template_name]

        response = self.get(posixpath.join("job_templates"), params={'per_page': 'all'})
        templates = response.json()["results"]

        for job in templates:
            self._template_cache[job["name"]] = job["id"]

        template_id = self._template_cache.get(template_name)
        if not template_id:
            raise ForemanAPIError(code=404, text=f"Job template '{template_name}' not found")

        logging.debug(f"Template id for [{template_name}] is [{template_id}]")
        return template_id

    def send_job_invocation(self, task_name, vm_name, **inputs):
        """
        Send a job invocation for a specific task and VM.
        :param task_name: str
        :param vm_name: str
        :param **inputs: kwargs
        :return job_id
        """
        logging.debug('Reached send_job_invocation')
        task_configs = {
            "resize_partition": {
                "template_name": "Run \"cdt-resize-partition\" role CDT",
                "description": "Partition Resizing"
            }
        }

        config = task_configs.get(task_name)
        if not config:
            raise ForemanAPIError(code=404, text=f"Unknown task: {task_name}")

        logging.debug(f"config for [{task_name}] is [{config}]")

        template_id = self.get_job_template_id(config["template_name"])

        payload = {
            "job_invocation": {
                "job_template_id": template_id,
                "targeting_type": "static_query",
                "search_query": f'name = "{vm_name}"',
                "description_format": config["description"],
                "inputs": inputs,
                "ansible": {
                    "tags": "",
                    "tags_flag": "include"
                }
            }
        }

        logging.debug(f"About to send job invocations with following request [{payload}]")
        response = self.post(
            posixpath.join("job_invocations"),
            headers=self.headers,
            json=payload
        )

        return response.json()["id"]

    def is_job_invocation_success(self, job_id, timeout=300, poll_interval=5):
        """
        Get a job status by given id.
        :param job_id: str
        :param timeout: int
        :param poll_interval: int
        :return status: bool
        """
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise ForemanAPIError(code=500, text=f"Job {job_id} timed out after {timeout} seconds")
            response = self.get(posixpath.join("job_invocations", str(job_id)))
            is_pending = bool(response.json().get("pending", False))
            if not is_pending:
                break
            logging.debug(f"job still pending, sleeping for {poll_interval} second")
            sleep(poll_interval)

        return bool(response.json().get("succeeded", False))

    def get_parameter_value(self, hostname, parameter_name):
        """
        Get a parameter value by given parameter_name.
        :param hostname: str
        :param parameter_name: str or list/tuple - Single parameter name or list/tuple of parameter names
        :return: dict or None - Dict of {name: value} for found parameters, None if none found
        """
        host_info = self.get_host_info(hostname=hostname)
        host_parameters = host_info.get("parameters")
        if not host_parameters:
            return None

        result = {}
        if isinstance(parameter_name, str):
            for host_parameter in host_parameters:
                if host_parameter["name"] == parameter_name:
                    result[host_parameter["name"]] = host_parameter["value"]
                    return result
            return None

        elif isinstance(parameter_name, (list, tuple)):
            param_set = set(parameter_name)
            for host_parameter in host_parameters:
                if host_parameter["name"] in param_set:
                    result[host_parameter["name"]] = host_parameter["value"]
            return result if result else None

        return None

    def set_parameter_value(self, hostname, parameter_name, parameter_value, auto_create=False):
        """
        Set a parameter value by given parameter_name and parameter_value.
        Also, auto_create option will automatically create the parameter if not appear.
        :param hostname: str
        :param parameter_name: str
        :param parameter_value: str
        :param auto_create: bool
        """
        logging.debug('Reached set_parameter_value')
        payload = {
            "parameter": {
                "name": parameter_name,
                "value": parameter_value
            }
        }

        if self.get_parameter_value(hostname=hostname, parameter_name=parameter_name) is None:
            logging.debug(f"parameter {parameter_name} is not created yet")
            if auto_create:
                logging.debug(f"creating parameter {parameter_name}")
                self.post(posixpath.join("hosts", hostname, "parameters"), headers=self.headers, json=payload)
            return

        logging.debug(f"updating {parameter_name}")
        self.put(posixpath.join("hosts", hostname, "parameters", parameter_name), headers=self.headers, json=payload)

    def get_host_ansible_roles(self, hostname):
        """
        Get ansible role from host.
        :param hostname: str
        """
        logging.debug('Reached get_host_ansible_roles')

        response = self.get(posixpath.join("hosts", hostname, "ansible_roles"), headers=self.headers)
        roles = response.json()

        return roles

    def get_ansible_role(self, roles=None):
        """
        Get ansible role id by its name.
        :param role_name: str
        """
        logging.debug('Reached get_ansible_role')

        if not roles:
            params = {'per_page': 'all'}
            response = self.get(posixpath.join("ansible", "api", "ansible_roles"), params=params, headers=self.headers).json()

            logging.debug(f"About to return {response.get('subtotal')} roles")
            return response.get("results")

        params = {'search': None}

        if isinstance(roles, (str, int)):
            roles = [roles]

        query = []
        for role in roles:
            if isinstance(role, str):
                query.append(f"name={role}")
            elif isinstance(role, int):
                query.append(f"id={role}")
            else:
                raise ForemanAPIError(f"Invalid role type: {type(role)}")

        params["search"] = " or ".join(query)

        logging.debug(f"Search param is {params.get('search')}")
        response = self.get(posixpath.join("ansible", "api", "ansible_roles"), params=params, headers=self.headers).json()

        logging.debug(f"About to return {response.get('subtotal')} roles")
        return response.get("results")

    def assign_ansible_roles(self, hostname, roles):
        """
        Assign an ansible roles and override value by given role_id and kwargs to specific hostname.
        :param hostname: str
        :param roles: list/str/int
        """
        logging.debug('Reached assign_ansible_roles')
        logging.debug(f'Hostname: [{hostname}]')
        logging.debug(f'Roles: [{roles}]')

        role_ids = []
        role_names = []

        if isinstance(roles, (str, int)):
            roles = [roles]

        roles = self.get_ansible_role(roles)
        for role in roles:
            role_ids.append(role.get("id"))
            role_names.append(role.get("name"))

        payload = {
            "ansible_role_ids": role_ids
        }

        # Assign ansible roles
        logging.debug(f'About to set roles {role_names}')
        self.post(posixpath.join("hosts", hostname, "assign_ansible_roles"), headers=self.headers, json=payload)

    def assign_ansible_roles_and_override(self, hostname, roles):
        """
        Assign an ansible roles and override value by given role_id and kwargs to specific hostname.
        :param hostname: str
        :param roles: dict
        """
        logging.debug('Reached assign_ansible_roles_and_override')
        logging.debug(f'Hostname: [{hostname}]')
        logging.debug(f'Roles: [{roles}]')

        role_ids = []
        updated_dict = {}

        if not isinstance(roles, dict):
            raise ForemanAPIError(code=400, text="Input must be in dict")

        temp_roles = []
        for role, variable in roles.items():
            temp_roles.append(role)

        new_roles = self.get_ansible_role(temp_roles)
        for new_role in new_roles:
            role_ids.append(new_role.get("id"))
            if not roles.get(new_role.get("id")):
                continue

            roles[new_role.get("name")] = roles.pop(new_role.get("id"))

        payload = {
            "ansible_role_ids": role_ids
        }

        for key, values in roles.items():
            params = {"search": f"ansible_role={key}", "per_page": "all"}

            variables = self.get(posixpath.join("ansible", "api", "ansible_variables"), params=params).json()["results"]
            valid_params = {v["parameter"]: v["id"] for v in variables}

            missing = [p for p in values.keys() if p not in valid_params]
            if missing:
                raise ForemanAPIError(code=400, text=f"Role '{key}' missing variables: {', '.join(missing)}")

            for param_name, param_value in values.items():
                variable_id = valid_params[param_name]
                updated_dict[f"{variable_id}-{param_name}"] = param_value

        # Assign ansible roles
        logging.debug(f'About to set roles {roles}')
        self.post(posixpath.join("hosts", hostname, "assign_ansible_roles"), headers=self.headers, json=payload)

        for key, value in updated_dict.items():
            payload = {
                "ansible_variable_id": key,
                "override_value": {
                    "match": f"fqdn={hostname}",
                    "value": value
                }
            }
            logging.debug(f'About to override ansible variables {key} with value {value}')

            self.post(posixpath.join("ansible", "api", "ansible_override_values"), headers=self.headers, json=payload)
            sleep(1)