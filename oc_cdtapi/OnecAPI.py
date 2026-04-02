"""
OnecAPI - Improved client for interacting with the 1C API.
"""

from operator import itemgetter
import logging

from oc_cdtapi.API import HttpAPI, HttpAPIError


class OnecAPI(HttpAPI):
    """
    API client for interacting with the 1C system.
    """
    
    _env_prefix = "ONEC"

    service_name = "Onec"
    
    headers = {
        "Accept": "application/json;version=2",
        "Content-Type": "application/json"
    }
    
    MAX_CLIENTS_FOR_LICENSE_QUERY = 100
    MAX_URL_LENGTH = 2048

    def __init__(self, *args, **kwargs):
        """Initialize the OnecAPI client with default settings."""
        super().__init__(*args, **kwargs)

    def get_clients_by_query(self, request_params):
        """
        Retrieve clients from 1C based on query parameters.
        
        Args:
            request_params: Dictionary of query parameters. Values can be strings
                          or lists of strings for multi-value parameters.
        
        Returns:
            Tuple of (client_info, error_message):
                - client_info: List of client dictionaries sorted by 'code', or None on error
                - error_message: Error description string, or None on success
        
        Examples:
            >>> api = OnecAPI(base_url="https://api.example.com")
            >>> clients, error = api.get_clients_by_query({"status": "active"})
            >>> if error:
            ...     print(f"Error: {error}")
            ... else:
            ...     print(f"Found {len(clients)} clients")
        """
        logging.debug("Retrieving clients with params: %s", request_params)
        
        try:
            query_string = self._build_query_string(request_params)
            logging.debug("Generated query string: %s", query_string)
            
            response = self.get("clients", params={"query": query_string})
            
            if response.status_code == 200:
                return self._parse_clients_response(response)
            else:
                error_msg = (
                    f"Client request failed with status {response.status_code}. "
                    f"Response: {response.json()}"
                )
                logging.warning(error_msg)
                return None, error_msg
                
        except HttpAPIError as e:
            error_msg = f"Error communicating with 1C API: {e}"
            logging.error(error_msg)
            return None, error_msg

    def get_clients_licenses(self, clients=None):
        """
        Retrieve license information for specified clients.
        
        Args:
            clients: Optional list of client codes. If None or exceeds 100 clients,
                    retrieves all licenses to avoid URL length limitations.
        
        Returns:
            Tuple of (licenses, error_message):
                - licenses: List of license dictionaries, or None on error
                - error_message: Error description string, or None on success
        
        Note:
            Due to GET request URL length limits (~2048 chars), queries are
            limited to 100 clients. Larger requests retrieve all licenses.
        """
        logging.debug("Retrieving client licenses for %s clients", 
                    len(clients) if clients else "all")
        
        query_params = self._build_license_query_params(clients)
        
        try:
            response = self.get('clientLicenses', params={"client": query_params})
            return response.json(), None
            
        except HttpAPIError as e:
            error_msg = f"Error communicating with 1C API: {e}"
            logging.error(error_msg)
            return None, error_msg
    
    def get_licenses_codes(self, client_code=None):
        """
        Retrieve active license codes for a specific client.
        
        Args:
            client_code: The client's unique code identifier. If None or empty,
                        returns an empty list.
        
        Returns:
            Tuple of (license_codes, error_message):
                - license_codes: List of active license code strings, or None on error
                - error_message: Error description string, or None on success
        
        Examples:
            >>> api = OnecAPI(base_url="https://api.example.com")
            >>> codes, error = api.get_licenses_codes("CLIENT123")
            >>> if error:
            ...     print(f"Error: {error}")
            ... else:
            ...     print(f"Found licenses: {codes}")
        """
        logging.debug("Retrieving license codes for client: %s", client_code)
        
        if not client_code:
            logging.debug("No client code provided, returning empty list")
            return [], None
        
        try:
            response = self.get('components', params={"client": client_code})
            
            if response.status_code == 200:
                licenses = response.json()
                license_codes = [
                    license["code"] 
                    for license in licenses 
                    if license.get("code")
                ]
                logging.debug("Found %d license codes", len(license_codes))
                return license_codes, None
            else:
                error_msg = (
                    f"Components request failed with status {response.status_code} "
                    f"for endpoint: {self.root}/components?client={client_code}"
                )
                logging.error(error_msg)
                return None, error_msg
                
        except HttpAPIError as e:
            error_msg = f"Error communicating with 1C API: {e}"
            logging.error(error_msg)
            return None, error_msg
    
    def _build_query_string(self, params):
        """
        Build a URL query string from parameter dictionary.
        
        Args:
            params: Dictionary where values can be strings or lists of strings
        
        Returns:
            Formatted query string without leading '&'
        """
        query_parts = []
        
        for key, value in params.items():
            if not value:
                continue
            
            if isinstance(value, str) or not hasattr(value, '__iter__'):
                query_parts.append(f"{key}={value}")
            
            else:
                query_parts.extend(f"{key}={item}" for item in value)
        
        return '&'.join(query_parts)
    
    def _build_license_query_params(self, clients):
        """
        Build query parameters for license requests with URL length consideration.
        
        Args:
            clients: List of client codes or None
        
        Returns:
            Pipe-separated string of client codes, or None for all clients
        """
        if not clients or len(clients) > self.MAX_CLIENTS_FOR_LICENSE_QUERY:
            return None
        
        return "|".join(clients)
    
    def _parse_clients_response(self, response):
        """
        Parse and validate the clients API response.
        
        Args:
            response: HTTP response object from clients endpoint
        
        Returns:
            Tuple of (parsed_clients, error_message)
        """
        try:
            clients_data = response.json()
            
            sorted_clients = sorted(clients_data, key=itemgetter('code'))
            logging.debug("Successfully retrieved %d clients", len(sorted_clients))
            return sorted_clients, None
            
        except KeyError as e:
            error_msg = (
                f"Corrupted client data from 1C - missing 'code' field: "
                f"{response.json()}"
            )
            logging.error(error_msg)
            return None, error_msg
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid JSON response from 1C: {e}"
            logging.error(error_msg)
            return None, error_msg