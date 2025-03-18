import json
import logging
import posixpath
import re

from oc_cdtapi.API import HttpAPI, HttpAPIError
from collections import namedtuple, defaultdict
from datetime import datetime, timedelta
from packaging import version

class ForemanAPIError(HttpAPIError):
    pass


class ForemanAPI(HttpAPI):
    """
    A simple client for Foreman's REST API
    """

    _error = ForemanAPIError
    _env_prefix = "FOREMAN"

    headers = {"Accept": "version=2,application/json", "Content-Type": "application/json"}

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
        if not req.startswith("foreman_puppet"):
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
            raise ForemanAPIError("The owner id is not specified")

        if not default_params["name"]:
            raise ForemanAPIError("The hostname is not specified")

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
            raise ForemanAPIError("The owner id is not specified")

        if not default_params["name"]:
            raise ForemanAPIError("The hostname is not specified")

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
        response = self.post(posixpath.join('foreman_puppet', 'api', 'hosts', hostname, 'puppetclass_ids'), headers=self.headers, data=params)

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
            raise ForemanAPIError("500 - Incorrect power action was provided")

        params = json.dumps({"power_action": action})
        request = self.put(posixpath.join("hosts", hostname, "power"), headers=self.headers, data=params)

    def host_power_v2(self, hostname, action):
        """
        Turns on/off power on the host
        """
        logging.debug('Reached host_power_v2')
        actions = ["on", "off"]
        if action not in actions:
            raise ForemanAPIError("500 - Incorrect power action was provided")
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
                return hostgroup.get ('id')
        
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
            raise ForemanAPIError(f"The owner [{owner}] is not found")
            
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
