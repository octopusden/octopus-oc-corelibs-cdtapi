import logging
from urllib.parse import quote

from oc_cdtapi import API
from oc_cdtapi.API import HttpAPIError

_SUPPORTED_VERSIONS = ("v1", "v2")

class PostgresAPI(API.HttpAPI):
    _env_prefix = 'PSQL'
    _env_token = 'TOKEN'

    def __init__(self, *args, api_version: str = "v1", **kwargs):
        """
        Args:
            api_version: API version to use for task endpoints — ``"v1"`` (default)
                         targets ``/rest/api/1/tasks`` while ``"v2"`` targets
                         ``/api/v2/tasks``.  All non-task endpoints always use v1.
        """
        if api_version not in _SUPPORTED_VERSIONS:
            raise ValueError(f"api_version must be one of {_SUPPORTED_VERSIONS}, got {api_version!r}")
        self._api_version = api_version
        super().__init__(*args, **kwargs)

    @property
    def _tasks_base(self) -> str:
        """URL prefix for task endpoints, selected by api_version."""
        return "api/v2" if self._api_version == "v2" else "rest/api/1"

    def _unwrap_tasks(self, response) -> list:
        """
        Normalise a tasks response to a plain list regardless of API version.

        v1 returns a list directly.
        v2 returns ``{"success": true, "data": {"items": [...], ...}}``.
        """
        body = response.json()
        if self._api_version == "v2":
            return body.get("data", {}).get("items", [])
        return body

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
        Create a new task entry (v1 and v2).

        Args:
            request (dict): Task payload. v2 requires ``hostname``, ``action_code``,
                ``status``, ``username``, and ``task_content``.

        Returns:
            requests.Response: The raw response object.

        Example:
            >>> api = PostgresAPI(api_version="v2")
            >>> result = api.post_tasks({
            ...     "hostname": "worker-01",
            ...     "action_code": "DEPLOY",
            ...     "status": "PENDING",
            ...     "username": "user1",
            ...     "task_content": {"version": "2.1.0"},
            ... })
            >>> print(result.status_code)
            201
        """
        req = f"{self._tasks_base}/tasks"
        res = self.post(req, json=request)
        logging.debug("post_tasks via %s", self._tasks_base)
        return res

    def update_task(self, task_id, request):
        """
        Update a task by ID (v1 and v2).

        Args:
            task_id (int): The task ID to update.
            request (dict): Fields to update.

        Returns:
            requests.Response: The raw response object.

        Example:
            >>> api = PostgresAPI(api_version="v2")
            >>> result = api.update_task(1, {"status": "DONE"})
            >>> print(result.status_code)
            200
        """
        req = f"{self._tasks_base}/tasks/{task_id}"
        res = self.put(req, json=request)
        logging.debug("update_task %s via %s", task_id, self._tasks_base)
        return res

    def get_task_by_id(self, task_id):
        """
        Get a single task by ID.

        - **v1**: ``GET /rest/api/1/tasks?id=<task_id>`` — filters via query param,
          returns the first item from the list.
        - **v2**: ``GET /api/v2/tasks/<task_id>`` — dedicated path-param endpoint,
          returns the task directly from ``response["data"]``.

        Args:
            task_id (int): The task ID.

        Returns:
            dict | None: The task dict, or ``None`` if not found.
        """
        try:
            if self._api_version == "v2":
                req = f"api/v2/tasks/{task_id}"
                res = self.get(req)
                return res.json().get("data")
            else:
                req = "rest/api/1/tasks"
                res = self.get(req, params={"id": task_id})
                items = res.json()
                return items[0] if items else None
        except HttpAPIError as e:
            if e.code == 404:
                return None
            raise

    def get_task_by_id_and_username(self, task_id, username):
        """
        Get a single task by ID and username (v1 and v2).

        Returns the first matching task dict, or ``None`` if not found.

        Args:
            task_id (int): The task ID.
            username (str): The owner username.

        Returns:
            dict | None
        """
        try:
            req = f"{self._tasks_base}/tasks"
            res = self.get(req, params={"id": task_id, "username": username})
        except HttpAPIError as e:
            if e.code == 404:
                return None
            raise

        items = self._unwrap_tasks(res)
        return items[0] if items else None

    def get_task_custom_filter(self, **kwargs):
        """
        Get tasks matching arbitrary filter params (v1 and v2).

        Returns a plain list of task dicts regardless of API version,
        so callers don't need to change when switching versions.

        Args:
            **kwargs: Filter parameters (e.g. ``status="Approved"``,
                ``action_code="create"``).

        Returns:
            list[dict]

        Example:
            >>> api = PostgresAPI(api_version="v2")
            >>> tasks = api.get_task_custom_filter(status="PENDING")
        """
        try:
            req = f"{self._tasks_base}/tasks"
            res = self.get(req, params=kwargs)
        except HttpAPIError as e:
            if e.code == 404:
                return []
            raise

        return self._unwrap_tasks(res)

    def get_tasks_paginated(self, page: int = 1, page_size: int = 20, **filters):
        """
        Get tasks with full pagination metadata — **v2 only**.

        Returns the raw ``data`` dict from the v2 envelope:
        ``{"page": 1, "page_size": 20, "total": N, "items": [...]}``.

        Raises:
            RuntimeError: If called on a v1 instance.

        Args:
            page (int): Page number (1-based).
            page_size (int): Items per page (max 100).
            **filters: Optional filter params (``status``, ``action_code``, ``username``).

        Returns:
            dict: Pagination envelope with ``items``, ``total``, ``page``, ``page_size``.

        Example:
            >>> api = PostgresAPI(api_version="v2")
            >>> result = api.get_tasks_paginated(page=1, page_size=10, status="PENDING")
            >>> print(result["total"])
            42
            >>> print(result["items"][0]["hostname"])
            'worker-node-01'
        """
        if self._api_version != "v2":
            raise RuntimeError("get_tasks_paginated is only available with api_version='v2'")

        params = {"page": page, "page_size": page_size, **filters}
        res = self.get("api/v2/tasks", params=params)
        logging.debug("get_tasks_paginated page=%s page_size=%s filters=%s", page, page_size, filters)
        return res.json().get("data", {})

    def get_all_placements(self, visible_on_ui: bool = None) -> list:
        """
        Get all placements — always uses v2.

        Each item contains: ``id``, ``name``, ``visible_on_ui``, ``requires_wrap``,
        ``backup``, ``provider_resources``, and a nested ``provider`` dict with
        ``id`` and ``name``.

        Args:
            visible_on_ui: When ``True``, only return placements visible on the UI.
                           ``None`` (default) returns all.

        Returns:
            list[dict]: All matching placement dicts.

        Example:
            >>> placements = api.get_all_placements(visible_on_ui=True)
            >>> print(placements[0]["provider"]["name"])
            'OpenStack'
        """
        params = {}
        if visible_on_ui is not None:
            params["visible_on_ui"] = visible_on_ui
        res = self.get("api/v2/placements", params={"page_size": -1, **params})
        logging.debug("get_all_placements visible_on_ui=%s", visible_on_ui)
        return res.json().get("data", {}).get("items", [])

    def get_placement(self, name: str) -> list:
        """
        Get placements by name — always uses v2 (placements are v2-only).

        Returns a plain list of placement dicts matching the given name.
        Each item contains: ``id``, ``name``, ``visible_on_ui``, ``requires_wrap``,
        ``backup``.

        .. note::
            The v2 placements model does not include a ``domain`` field.  If your
            calling code accesses ``placement["domain"]``, that field must first be
            added to the ``Placements`` model and ``Read`` DTO in
            ``idp-postgres-api-service``.

        Args:
            name (str): Placement name to filter by.

        Returns:
            list[dict]: Matching placement dicts (empty list if none found).

        Example:
            >>> placements = api.get_placement("dc1-vmware")
            >>> print(placements[0]["id"])
            3
        """
        res = self.get("api/v2/placements", params={"name": name})
        logging.debug("get_placement name=%s", name)
        return res.json().get("data", {}).get("items", [])

    def get_placement_by_id(self, placement_id: int) -> dict:
        """
        Get a single placement by its ID — always uses v2.

        Args:
            placement_id (int): The placement's primary key.

        Returns:
            dict: The placement dict, including nested ``provider``.

        Raises:
            requests.HTTPError: If the server returns 404 or another error status.

        Example:
            >>> placement = api.get_placement_by_id(3)
            >>> print(placement["name"])
            'dc1-vmware'
        """
        res = self.get(f"api/v2/placements/{placement_id}")
        logging.debug("get_placement_by_id id=%s", placement_id)
        return res.json().get("data", {})

    def get_clients_list(self):
        """
        Get a clients list.

        This method sends a GET request to get a client list including the ftp upload option by code.

        Returns:
            requests.Response: The response object from the API call.

        Example:
            >>> code = 2
            >>> result = self.get_clients_list()
            >>> print(result)
            {
                "can_receive": true,
                "code": "_TEST_1",
                "country": "TEST_COUNTRY",
                "is_active": false,
                "language": "en",
                "should_encrypt": true
            },
            {
                "can_receive": true,
                "code": "_TEST_2",
                "country": "TEST_COUNTRY",
                "is_active": false,
                "language": "en",
                "should_encrypt": true
            },
        """
        req = "rest/api/1/clients"
        res = self.get(req)

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

    def post_new_component(self, payload):
        """
        Post new component to the ci database.

        This method sends a POST request to add new component into ci database.

        Args:
            payload : New component payload.

        Returns:
            requests.Response: The response object from the API call.

        Example:
            >>> payload = {
                        "ci_type_id": "NEWDSTR",
                        "ci_type_group_id": "NEW",
                        "name": "New component",
                        "is_standard": "Y",
                        "is_deliverable": True,
                        "regexp": "test.regexp.NEWDSTR:dstr:com",
                        "loc_type_id": "NXS",
                        "dms_id": "NEWDSTR"
            }
            >>> result = self.post_new_component(payload)
            >>> print(result.status_code)
            200
        """
        req = f"rest/api/1/manage_citype"
        res = self.post(req, json=payload)
        logging.debug(f'Using post_manage_citype to register new component')

        return res

    def get_client_distributions(self, code, citype):
        """
        Retrieve distribution information for a client.

        Sends a GET request to the API to obtain distribution data
        associated with a specific client and CI type.

        Args:
            code (str): Unique client identifier.
            citype (str): CI type used to filter distributions.

        Returns:
            dict: Parsed JSON response containing client distribution data.

        Raises:
            requests.HTTPError: If the API request fails.

        Example:
            >>> code = "client_code"
            >>> citype = "citype"
            >>> result = self.get_client_distributions(code, citype)
            >>> print(result)
            [...]
        """
        req = f"rest/api/1/clients/{quote(code, safe='')}/distributions"
        res = self.get(req, params={'citype': citype})

        return res.json()
