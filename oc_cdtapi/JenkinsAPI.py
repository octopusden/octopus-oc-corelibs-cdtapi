# requires python-requests rpm package
from enum import Enum
import requests
from .API import HttpAPI, HttpAPIError
from string import Template
import json
from collections import namedtuple, OrderedDict
import re
import xml.etree.ElementTree as ET
import posixpath
import sys


class JenkinsError(HttpAPIError):
    def __str__(self):
        return 'Error communicating with Jenkins: ' + self.text + ': Code ' + str(self.code) + ' ' + self.url


class Jenkins(HttpAPI):
    """
    Simple and easy-to-use Jenkins interface

    >>> def test(port):
    ...     jenk = Jenkins('http://127.0.0.1:'+str(port))
    ...     jenk.disable_job('job.to_disable')
    ...     jenk.enable_job('job.to_enable')
    ...     jenk.delete_job('job.to_delete')
    ...     jenk.get_job('job.to_get')
    ...     jenk.put_job('job.to_put','this is a job')
    ...
    >>> from TestServer import test_wrapper
    >>> test_wrapper(test,6)
    "POST /job/job.to_disable/disable HTTP/1.1" 200 -
    "POST /job/job.to_enable/enable HTTP/1.1" 200 -
    "POST /job/job.to_delete/doDelete HTTP/1.1" 200 -
    "GET /job/job.to_get/config.xml/api/json HTTP/1.1" 200 -
    "GET /job/job.to_put/config.xml/api/json HTTP/1.1" 200 -
    "POST /job/job.to_put/config.xml HTTP/1.1" 200 -

    """

    _error = JenkinsError
    _env_prefix = 'JENKINS'

    def re(self, req):
        if req and req.startswith('!'):
            req = req.lstrip('!')
            return posixpath.join(self.root, req)

        return posixpath.join(self.root, req, 'api', 'json')

    def post(self, req, *vargs, **kvargs):
        # We need all post requests to be processed in a different way in re(),
        # but do not wan't to rewrite post(). So we pass a little flag to be checked in re()
        return super(Jenkins, self).post('!' + req, *vargs, **kvargs)

    def list_jobs(self, prefix=None, suffix=None):
        """Gets job list"""
        jobs = self.get('', params={'tree': 'jobs[name]'})
        return filter(lambda x: (not prefix or x.startswith(prefix)) and (not suffix or x.endswith(suffix)),
                      map(lambda x: x['name'], jobs.json().get('jobs', [])))

    def get_node(self, node):
        """Gets config.xml for specific slave"""
        config = self.get(posixpath.join('computer', node, 'config.xml'))
        return config.text

    def put_node(self, node, config):
        """Saves config.xml for a node (or creates new node)"""
        request = posixpath.join('computer', node, 'config.xml')
        params = None
        headers = {'content-type': 'application/xml'}

        try:
            self.get_node(node)
        except JenkinsError as e:
            if e.code == 404:
                request = posixpath.join('computer', 'doCreateItem')
            params = {'name': node}

        if self.readonly:
            return None

        put = self.post(request, data=config, params=params, headers=headers)
        return put

    def delete_node(self, node):
        """Deletes node from CI"""
        if self.readonly:
            return None
        return self.post(posixpath.join('computer', node, 'doDelete'))

    def get_node_label_from_config(self, config):
        """
        Get the exact XML tag value with XPATH: label
        :param self: self reference
        :param config: xml string with a configuration of node
        :return: <label> tag text
        """
        obj_xml = ET.fromstring(config)
        xml_tag = obj_xml.find('label')

        if (xml_tag is None) or (xml_tag.text is None) or (len(xml_tag.text.strip()) == 0):
            return ""

        return xml_tag.text

    def get_node_label(self, node, config=None):
        if not config:
            config = self.get_node(node)
        return self.get_node_label_from_config(config).split(' ')

    def set_node_label_in_config(self, config, label):
        """
        set <label> tag in XML config
        :param self: self reference
        :param config: string with XML node configuration
        :return: string with edited 'config' with <lable> tag content set to 'label'
        """
        obj_xml = ET.fromstring(config)
        xml_tag = obj_xml.find('label')

        if (xml_tag is None):
            xml_tag = ET.SubElement(obj_xml, 'label')

        xml_tag.text = label

        return ET.tostring(obj_xml, encoding='utf8')

    def set_node_label(self, node, label):
        config = self.get_node(node)
        config = self.set_node_label_in_config(config, ' '.join(label))
        return self.put_node(node, config)

    def enable_node(self, job):
        if self.readonly:
            return None
        return self.post(posixpath.join('computer', job, 'enable'))

    def disable_node(self, job):
        if self.readonly:
            return None
        return self.post(posixpath.join('computer', job, 'disable'))

    def is_node_idle(self, node):
        """Retrieve 'idle' attribute of a node via newer JSON API (may require Jenkins 2.x)."""
        return self.get(posixpath.join("computer", node, "api", "json")).json().get('idle')

    def list_nodes(self):
        """
        List all active nodes (except master one)
        :return: List of strings with node names, possible empty
        """
        raw_data = self.get("computer", params={"tree": "computer[displayName]"})
        str_data = raw_data.text

#        return map( lambda x: x[ "displayName" ], json.loads( self.get( "computer", params = { "tree" : "computer[displayName]" } ).text )[ "computer" ] );
        return [x["displayName"] for x in json.loads(str_data)["computer"]]

    def job_xml_enable(self, config):
        """
        Enables jenkins job by modifying XML tag (XPATH=) in the configuration
        :param self: self reference
        :param config: xml string from a config
        :return: xml string with <disabled> tag value modified to 'true'
        """
        obj_xml = ET.fromstring(config)
        xml_tag = obj_xml.find('disabled')

        if xml_tag is None:
            return config

        xml_tag.text = "false"

        return ET.tostring(obj_xml, encoding='utf8')

    def copy_job(self, config, j_name, parameters={}, enabled=True, use_template=False):
        """Create or update job by template"""

        if config[0] != '<':
            config = self.get_job(config)
        parameters['name'] = j_name
        if enabled:
            config = self.job_xml_enable(config)

        cfg_type = str(type(config))
        if cfg_type.find('byte') != -1:
            config = str(config, 'UTF-8')

        if use_template:
            config = Template(config).safe_substitute(parameters)
        else:
            config = config.format(**parameters)

        put = self.put_job(j_name, config)
        #		if enabled: self.enable_job(j_name)
        return put

    def get_job(self, job):
        """Gets config.xml for a job"""
        config = self.get(posixpath.join('job', job, 'config.xml'))
        return config.text

    def put_job(self, job, config):
        """Saves config.xml for a job (or creates new job)"""
        request = posixpath.join('job', job, 'config.xml')
        params = None
        headers = {'content-type': 'application/xml'}
        try:
            self.get_job(job)
        except JenkinsError as e:
            if e.code == 404:
                request = 'createItem'
            params = {'name': job}

        if self.readonly:
            return None
        put = self.post(request, data=config, params=params, headers=headers)
        return put

    def enable_job(self, job):
        if self.readonly:
            return None
        return self.post(posixpath.join('job', job, 'enable'))

    def disable_job(self, job):
        if self.readonly:
            return None
        return self.post(posixpath.join('job', job, 'disable'))

    def delete_job(self, job):
        if self.readonly:
            return None
        return self.post(posixpath.join('job', job, 'doDelete'))

    def run_job(self, job, params=None):
        if self.readonly:
            return None
        if params == None:
            response = self.post(posixpath.join('job', job, 'build'))
        else:
            response = self.post(posixpath.join('job', job, 'buildWithParameters'), data=params)

        queue_item = QueueItem.from_jenkins_response(response, self)
        return queue_item

    def list_builds(self, node=None):
        """
        Get list of Builds which are currently build on the node given
        :param node: list only jobs building on the node specified
        :type node: string
        :return: dictionary with node_names as a key and list of jobs dictionaries building on the node as { "job_name": ... , "build_number" : ... }, list may be None
        """
        str_request = ""
        dict_parms = {"tree": "jobs[name,lastBuild[building,fullDisplayName,number,url,builtOn]]"}

        if node is not None:
            str_request = posixpath.join("computer", node)
            dict_parms["tree"] = "executors[idle,currentExecutable[idle,building,builtOn,number,fullDisplayName,url]]"

        response = self.get(str_request, params=dict_parms)
        dict_resp = json.loads(response.text)

        if node is not None:
            if len(dict_resp["executors"]) == 0:
                return {node: list()}

            ls_jobs = map(lambda x: {"name": None, "lastBuild": (
                None if x["idle"] else x["currentExecutable"])}, dict_resp["executors"])

        else:
            ls_jobs = dict_resp["jobs"]

        dict_result = dict()

        for dict_job in ls_jobs:
            if "lastBuild" not in dict_job or dict_job["lastBuild"] is None or not dict_job["lastBuild"]["building"]:
                continue  # inactive build, out of interes

            str_job_name = dict_job["name"]

            if not str_job_name:
                str_job_name = dict_job["lastBuild"]["url"].split(
                    posixpath.sep + "job" + posixpath.sep, 1)[1].split(posixpath.sep, 1)[0]

            str_builder_node = dict_job["lastBuild"]["builtOn"]

            if str_builder_node not in dict_result:
                dict_result[str_builder_node] = list()

            dict_result[str_builder_node].append(
                {"job_name": str_job_name, "build_nubmer": dict_job["lastBuild"]["number"]})

        return dict_result

    def list_queue(self):
        """
        Get queue items, perhaps empty if no jobs queued
        :return: list of QueueItems, possible empty
        """
        ls_result = list()
        obj_resp = self.get("queue")
        dict_resp = json.loads(obj_resp.text or {})

        if not 'items' in dict_resp:
            return ls_result

        for dict_task in dict_resp['items']:
            if not 'task' in dict_task:
                continue

            if not 'name' in dict_task['task']:
                continue

            if not 'id' in dict_task:
                continue

            ls_result.append(QueueItem(dict_task['id'], self, dict_task))

        return ls_result

    def unqueue_item(self, int_id):
        """
        remove item with ID given from queue
        :param int_id: id
        :type int_id: integer
        """
        if int_id is None or not isinstance(int_id, int):
            raise TypeError("Wrong type of arguments: int_id is not integer")

        try:
            self.post(posixpath.join('queue', 'cancelItem'), data={}, params={"id": int_id})
        except:
            pass  # since jenkins returns 404 code for this type of operation and it is normal


class BuildStatus(Enum):
    BUILDING = 0
    SUCCESS = 1
    FAILURE = 2
    ABORTED = 3
    UNSTABLE = 4
    NOT_BUILD = 5


class Build(object):
    """
    Class designating launched build with known number.
    """

    def __init__(self, job_name, build_number, jenkins_client):
        self.job_name = job_name
        self.build_number = build_number
        self.jenkins_client = jenkins_client
        self._build_status = BuildStatus.BUILDING

    def get_status(self):
        self._update_build_status()
        return self._build_status

    def _update_build_status(self):
        if self._build_status != BuildStatus.BUILDING:
            return self._build_status
        build_path = posixpath.join("job", self.job_name, str(self.build_number), 'api', 'json')
        response = self.jenkins_client.get(build_path)
        if response.status_code == 404:
            raise JenkinsError("No build exist at %s" % build_path)
        parsed_response = json.loads(response.text or "{}")
        status_value = parsed_response["result"]
        if not status_value:
            self._build_status = BuildStatus.BUILDING
        else:
            if sys.version_info.major == 2:
                self._build_status = getattr(BuildStatus, status_value)
            else:
                self._build_status = BuildStatus[status_value]


class QueueItem(object):
    """ 
    Class used to hold information about build request.
    Initially it only knows its queue id, which can be used to get concrete build later.
    """

    @classmethod
    def from_jenkins_response(cls, response, jenkins_client):
        location_url = response.headers["Location"]
        search_result = re.search(r'' + posixpath.join("queue", "item", "(?P<queue_id>\d+)"), location_url)
        queue_id = int(search_result.group("queue_id"))
        return QueueItem(queue_id, jenkins_client)

    def __init__(self, queue_id, jenkins_client, dict_details=None):
        """
        :param resource: id in build queue (assigned at build launch request)
        :param required: jenkins.Jenkins instance
        """
        self.queue_id = queue_id
        self.jenkins_client = jenkins_client
        self._build = None
        self._task = None

        if not dict_details:
            return

        if "task" in dict_details:
            self._task = dict_details["task"]

    @property
    def task(self):
        """
        :return: dictionary with task parameters - job name, url, color - as it returned by Jenkins
        """
        if not self._task:
            self._try_update_queue_status()
        return self._task

    @property
    def job_name(self):
        """
        :return: job name of the queue item
        """

        if not self._task:
            self._try_update_queue_status()

        if not self._task:
            return None

        if "url" not in self._task:
            self._try_update_queue_status()

        if "url" not in self._task:
            return None

        return self._task["url"].split(posixpath.sep + "job" + posixpath.sep, 1).pop().split(posixpath.sep, 1).pop(0)

    def is_running(self):
        self._try_update_queue_status()
        return bool(self._build)

    def get_build(self):
        self._try_update_queue_status()

        if self._build:
            return self._build
        
        raise BuildStatusException("Build is not started yet")

    def _try_update_queue_status(self):
        if self._build:
            return
        item_path = posixpath.join("queue", "item", str(self.queue_id), "api", "json")
        response = self.jenkins_client.get(item_path)
        if response.status_code == 404:
            raise JenkinsError("No queue item exist at %s" % item_path)
        parsed_response = json.loads(response.text or "{}")
        if "executable" in parsed_response:
            self._build = Build(parsed_response["task"]["name"],
                                parsed_response["executable"]["number"],
                                self.jenkins_client)

        if not self._task and "task" in parsed_response:
            self._task = parsed_response["task"]


class BuildStatusException(Exception):
    pass

