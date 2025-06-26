import logging
import os

from oc_cdtapi import API
from oc_cdtapi.API import HttpAPIError


class PostgresAPI(API.HttpAPI):
    _env_prefix = 'PSQL'
    _env_token = 'TOKEN'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_citypedms_by_citype_id(self, citype):
        """
        Retrieve citypedms information for a given CI type ID.

        This method fetches a list of citypedms entries containing id, ci_type_id,
        dms_id, and gav_template for the specified CI type ID.

        Args:
            citype (str): The CI type ID to query.

        Returns:
            dict: A dictionary containing citypedms information with the following keys:
                - id: The citypedms entry ID
                - ci_type_id: The CI type ID
                - dms_id: The DMS ID
                - gav_template: The GAV (Group:Artifact:Version) template

        Example:
            >>> citypedms = api.get_citypedms_by_citype_id("CI123")
            >>> print(citypedms['id'])
            'CP456'
        """
        req = f"rest/api/1/citypedms/{citype}"
        res = self.get(req).json()
        logging.debug(f'Using get_citypedms_by_citype_id to get information about {citype}')

        return res

    def get_citypedms_by_dms_id(self, dms_id):
        """
        Retrieve citypedms information for a given DMS ID.

        This method fetches a list of citypedms entries containing id, ci_type_id,
        dms_id, and gav_template for the specified DMS ID (component ID).

        Args:
            dms_id (str): The DMS ID (component ID) to query.

        Returns:
            dict: A dictionary containing citypedms information with the following keys:
                - id: The citypedms entry ID
                - ci_type_id: The CI type ID
                - dms_id: The DMS ID
                - gav_template: The GAV (Group:Artifact:Version) template

        Example:
            >>> citypedms = api.get_citypedms_by_dms_id("DMS789")
            >>> print(citypedms['gav_template'])
            'com.example:{artifact}:{version}'
        """
        req = f"rest/api/1/citypedms/{dms_id}?bycomponent=True"
        res = self.get(req)
        logging.debug(f'Using get_citypedms_by_dms_id to get information about {dms_id}')

        return res.json()

    def get_ci_type_by_code(self, request):
        """
        Retrieve a list of ci type based on the provided ci type code.

        This function queries the ci database and returns a ci type
        that match the specified code in the request.

        Args:
            code (string): A code containing search parameters. For example:
                NSDC

        Returns:
            dict: A dict of citype object matching the search criteria.

        Example:
            >>> request = 'NSDC'
            >>> citype = get_ci_type_by_code(request)
            >>> print(citype)
            {
                "code": "NSDC",
                "doc_artifactid": null,
                "is_deliverable": false,
                "is_standard": "N",
                "name": "NetServer distribution component",
                "rn_artifactid": null
            }
        """
        req = f"rest/api/1/citype/{request}"
        res = self.get(req)
        logging.debug(f'Using get_ci_type_by_code to get information about citype with code {request}')

        return res.json()

    def get_deliveries(self, request):
        """
        Retrieve a list of deliveries based on the provided search criteria.

        This function queries the delivery database and returns a list of deliveries
        that match the specified parameters in the request.

        Args:
            request (dict): A dictionary containing search parameters. For example:
                {
                    'gav': 'somegav',
                    'flag_approved': True
                }

        Returns:
            list: A list of delivery objects matching the search criteria.

        Example:
            >>> request = {'gav': 'group:artifact:version', 'flag_approved': True}
            >>> deliveries = get_delivery(request)
            >>> print(deliveries)
            [Delivery1, Delivery2, ...]
        """
        req = f"rest/api/1/deliveries"
        res = self.get(req, params=request)
        logging.debug(f'Using get_delivery_by_gav to get information about delivery with {request}')

        return res.json()

    def get_historicaldelivery(self, request):
        """
        Retrieve a list of historicaldelivery based on the provided search criteria.

        This function queries the delivery database and returns a list of deliveries
        that match the specified parameters in the request.

        Args:
            request (dict): A dictionary containing search parameters. For example:
                {
                    'gav': 'somegav',
                    'flag_approved': True
                }

        Returns:
            list: A list of delivery objects matching the search criteria.

        Example:
            >>> request = {'gav': 'group:artifact:version', 'flag_approved': True}
            >>> historicaldeliveries = get_historicaldelivery(request)
            >>> print(historicaldeliveries)
            [HistoricalDelivery1, HistoricalDelivery1, ...]
        """
        req = f"rest/api/1/historicaldeliveries"
        res = self.get(req, params=request)
        logging.debug(f'Using get_historicaldelivery to get information about {request}')

        return res.json()

    def update_delivery_by_gav(self, gav, json):
        """
        Update delivery information for a specific GAV (Group:Artifact:Version).

        This method sends a PUT request to update the delivery information
        associated with the provided GAV.

        Args:
            gav (str): The GAV (Group:Artifact:Version) identifier of the delivery to update.
            json (dict): A dictionary containing the updated delivery information.

        Returns:
            requests.Response: The response object from the API call.

        Example:
            >>> gav = "com.example:artifact:1.0.0"
            >>> update_data = {"status": "approved", "version": "1.0.1"}
            >>> response = api.update_delivery_by_gav(gav, update_data)
            >>> print(response.status_code)
            200
        """
        payload = {"gav": gav}
        req = f"rest/api/1/deliveries"
        res = self.put(req, json=json, params=payload)
        logging.debug(f'Using put_delivery to update information about {gav}')

        return res

    def post_historicaldelivery(self, request):
        """
        Create a new historical delivery entry.

        This method sends a POST request to create a new historical delivery
        record with the provided information.

        Args:
            request (dict): A dictionary containing the historical delivery information to be created.

        Returns:
            dict: The JSON response from the API, typically containing the created historical delivery information.

        Example:
            >>> new_delivery = {
            ...     "gav": "com.example:artifact:1.0.0",
            ...     "timestamp": "2023-04-01T12:00:00Z",
            ...     "status": "delivered"
            ... }
            >>> result = api.post_historicaldelivery(new_delivery)
            >>> print(result['id'])
            12345
        """
        req = f"rest/api/1/historicaldeliveries"
        res = self.post(req, json=request)
        logging.debug(f'Using post_historicaldelivery to create information')

        return res

    def post_tasks(self, request):
        """
        Create a new tasks entry.

        This method sends a POST request to create a new tasks
        record with the provided information.

        Args:
            request (dict): A dictionary containing the tasks information to be inserted.

        Returns:
            requests.Response: The response object from the API call.

        Example:
            >>> tasks = {
                          ... "status": "Completed",
                          ... "action_code": "create",
                          ... "commentary": "",
                          ... "task_content": {
                          ...   "hardware": {
                          ...     "memory_mb": 5120
                          ...   },
                          ...   "name": "hostname",
                          ...   "username": "username"
                          ... },
                          ... "jira_verification_ticket": "ticket_id",
                          ... "status_desc": "status"
                        }
            >>> result = api.post_tasks(tasks)
            >>> print(result.status_code)
            201
        """
        req = f"rest/api/1/tasks"
        res = self.post(req, json=request)

        return res

    def update_task(self, task_id, request):
        """
        Create a new tasks entry.

        This method sends a POST request to create a new tasks
        record with the provided information.

        Args:
            request (dict): A dictionary containing the tasks information to be inserted.

        Returns:
            requests.Response: The response object from the API call.

        Example:
            >>> task_id = 2
            >>> tasks = {
                          ... "status": "Completed",
                          ... "action_code": "create",
                          ... "commentary": "",
                          ... "task_content": {
                          ...   "hardware": {
                          ...     "memory_mb": 5120
                          ...   },
                          ...   "name": "hostname",
                          ...   "username": "username"
                          ... },
                          ... "jira_verification_ticket": "ticket_id",
                          ... "status_desc": "status"
                        }
            >>> result = api.update_task(tasks)
            >>> print(result.status_code)
            200
        """
        req = f"rest/api/1/tasks/{task_id}"
        res = self.put(req, json=request)

        return res

    def get_task_by_id(self, task_id):
        """
        Get a task by id.

        This method sends a GET request to get a task by desired id.

        Args:
            task_id (int): An integer of the task id.

        Returns:
            requests.Response: The response object from the API call.

        Example:
            >>> task_id = 2
            >>> result = api.get_task_by_id(task_id)
            >>> print(result.status_code)
            200
        """
        try:
            payload = {"id": task_id}
            req = f"rest/api/1/tasks"
            res = self.get(req, params=payload)
        except HttpAPIError as e:
            if e.code == 404:
                return None
            else:
                raise HttpAPIError(e)

        return res.json()[0]

    def get_task_by_id_and_username(self, task_id, username):
        """
        Get a task by id and username.

        This method sends a GET request to get a task by desired id.

        Args:
            task_id (int): An integer of the task id.

        Returns:
            requests.Response: The response object from the API call.

        Example:
            >>> task_id = 2
            >>> result = api.get_task_by_id(task_id)
            >>> print(result.status_code)
            200
        """
        try:
            payload = {"id": task_id, "username": username}
            req = f"rest/api/1/tasks"
            res = self.get(req, params=payload)
        except HttpAPIError as e:
            if e.code == 404:
                return None
            else:
                raise HttpAPIError(e)

        return res.json()[0]

    def get_task_custom_filter(self, **kwargs):
        """
        Get a task by custom filter.

        This method sends a GET request to get a task by custom filter.

        Args:
            **kwargs : Keyword arguments for filtering.

        Returns:
            requests.Response: The response object from the API call.

        Example:
            >>> task_id = 2
            >>> param = {"id": 1, "hostname": "test.com"}
            >>> result = api.get_task_custom_filter(**param)
            >>> print(result.status_code)
            200
        """
        try:
            req = f"rest/api/1/tasks"
            res = self.get(req, params=kwargs)
        except HttpAPIError as e:
            if e.code == 404:
                return []
            else:
                raise HttpAPIError(e)

        return res.json()

    def get_client_by_code(self, code):
        """
        Get a client by code.

        This method sends a GET request to get a client including the ftp upload option by code.

        Args:
            code : Client code.

        Returns:
            requests.Response: The response object from the API call.

        Example:
            >>> code = 2
            >>> result = self.get_client_by_code(code)
            >>> print(result.status_code)
            200
        """
        req = f"rest/api/1/clients/{code}"
        res = self.get(req)

        return res.json()