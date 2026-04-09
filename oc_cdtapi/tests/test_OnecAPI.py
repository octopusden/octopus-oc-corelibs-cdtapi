import unittest
from unittest.mock import patch, MagicMock
from oc_cdtapi.OnecAPI import OnecAPI, OnecError

class TestOnecAPI(unittest.TestCase):

    @patch('os.getenv')
    def setUp(self, mock_getenv):
        mock_getenv.return_value = 'dummy_token'
        self.api = OnecAPI()

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_clients_by_query_success(self, mock_get):
        """Test successful client query with single parameter"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'code': 'CLIENT001', 'name': 'Test Client 1', 'status': 'active'},
            {'code': 'CLIENT002', 'name': 'Test Client 2', 'status': 'active'}
        ]
        mock_get.return_value = mock_response

        request_params = {'status': 'active'}
        result, error = self.api.get_clients_by_query(request_params)

        self.assertIsNone(error)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['code'], 'CLIENT001')
        self.assertEqual(result[1]['code'], 'CLIENT002')
        mock_get.assert_called_once_with('clients', params={'query': 'status=active'})

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_clients_by_query_with_multiple_values(self, mock_get):
        """Test client query with list of values for same parameter"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'code': 'CLIENT001', 'name': 'Client 1'},
            {'code': 'CLIENT002', 'name': 'Client 2'}
        ]
        mock_get.return_value = mock_response

        request_params = {'status': ['active', 'pending'], 'country': 'US'}
        result, error = self.api.get_clients_by_query(request_params)

        self.assertIsNone(error)
        self.assertEqual(len(result), 2)
        # Verify query string contains all parameters
        call_args = mock_get.call_args
        query_string = call_args[1]['params']['query']
        self.assertIn('status=active', query_string)
        self.assertIn('status=pending', query_string)
        self.assertIn('country=US', query_string)

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_clients_by_query_empty_params(self, mock_get):
        """Test client query with empty parameter values"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'code': 'CLIENT001', 'name': 'Client 1'}
        ]
        mock_get.return_value = mock_response

        request_params = {'status': 'active', 'country': '', 'region': None}
        result, error = self.api.get_clients_by_query(request_params)

        self.assertIsNone(error)
        call_args = mock_get.call_args
        query_string = call_args[1]['params']['query']
        # Only non-empty values should be in query
        self.assertEqual(query_string, 'status=active')

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_clients_by_query_non_200_status(self, mock_get):
        """Test client query with non-200 response"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'error': 'Not found'}
        mock_get.return_value = mock_response

        request_params = {'status': 'active'}
        result, error = self.api.get_clients_by_query(request_params)

        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn('404', error)
        self.assertIn('Not found', error)

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_clients_by_query_missing_code_field(self, mock_get):
        """Test client query with corrupted data (missing code field)"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'name': 'Client without code', 'status': 'active'}
        ]
        mock_get.return_value = mock_response

        request_params = {'status': 'active'}
        result, error = self.api.get_clients_by_query(request_params)

        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn('Corrupted', error)
        self.assertIn('code', error)

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_clients_by_query_api_error(self, mock_get):
        """Test client query with API communication error"""
        mock_get.side_effect = OnecError("Connection timeout")

        request_params = {'status': 'active'}
        result, error = self.api.get_clients_by_query(request_params)

        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn('Error communicating', error)
        self.assertIn('Connection timeout', error)

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_clients_licenses_with_clients(self, mock_get):
        """Test getting licenses for specific clients (under 100)"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'client_code': 'CLIENT001', 'license': 'LIC001', 'status': 'active'},
            {'client_code': 'CLIENT002', 'license': 'LIC002', 'status': 'active'}
        ]
        mock_get.return_value = mock_response

        clients = ['CLIENT001', 'CLIENT002', 'CLIENT003']
        result, error = self.api.get_clients_licenses(clients)

        self.assertIsNone(error)
        self.assertEqual(len(result), 2)
        # Verify pipe-separated format
        call_args = mock_get.call_args
        client_param = call_args[1]['params']['client']
        self.assertEqual(client_param, 'CLIENT001|CLIENT002|CLIENT003')

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_clients_licenses_with_no_clients(self, mock_get):
        """Test getting all licenses when no clients specified"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'client_code': 'CLIENT001', 'license': 'LIC001'},
            {'client_code': 'CLIENT002', 'license': 'LIC002'}
        ]
        mock_get.return_value = mock_response

        result, error = self.api.get_clients_licenses(None)

        self.assertIsNone(error)
        self.assertEqual(len(result), 2)
        # Should pass None when no clients specified
        call_args = mock_get.call_args
        self.assertIsNone(call_args[1]['params']['client'])

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_clients_licenses_over_100_clients(self, mock_get):
        """Test getting licenses when client list exceeds 100 (URL length limit)"""
        mock_response = MagicMock()
        mock_response.json.return_value = [{'license': 'LIC001'}]
        mock_get.return_value = mock_response

        # Create list of 101 clients
        clients = [f'CLIENT{i:03d}' for i in range(101)]
        result, error = self.api.get_clients_licenses(clients)

        self.assertIsNone(error)
        # Should pass None to get all licenses when over limit
        call_args = mock_get.call_args
        self.assertIsNone(call_args[1]['params']['client'])

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_clients_licenses_api_error(self, mock_get):
        """Test license query with API error"""
        mock_get.side_effect = OnecError("Network error")

        clients = ['CLIENT001']
        result, error = self.api.get_clients_licenses(clients)

        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn('Error communicating', error)
        self.assertIn('Network error', error)

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_licenses_codes_success(self, mock_get):
        """Test getting license codes for a specific client"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'code': 'LIC001', 'name': 'License 1', 'status': 'active'},
            {'code': 'LIC002', 'name': 'License 2', 'status': 'active'},
            {'name': 'License without code', 'status': 'active'}  # Should be filtered out
        ]
        mock_get.return_value = mock_response

        result, error = self.api.get_licenses_codes('CLIENT001')

        self.assertIsNone(error)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 'LIC001')
        self.assertEqual(result[1], 'LIC002')
        mock_get.assert_called_once_with('components', params={'client': 'CLIENT001'})

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_licenses_codes_no_client_code(self, mock_get):
        """Test getting license codes with no client code provided"""
        result, error = self.api.get_licenses_codes(None)

        self.assertIsNone(error)
        self.assertEqual(result, [])
        mock_get.assert_not_called()

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_licenses_codes_empty_client_code(self, mock_get):
        """Test getting license codes with empty string client code"""
        result, error = self.api.get_licenses_codes('')

        self.assertIsNone(error)
        self.assertEqual(result, [])
        mock_get.assert_not_called()

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_licenses_codes_non_200_status(self, mock_get):
        """Test license codes query with non-200 response"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result, error = self.api.get_licenses_codes('CLIENT001')

        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn('500', error)
        self.assertIn('components', error)

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_licenses_codes_api_error(self, mock_get):
        """Test license codes query with API communication error"""
        mock_get.side_effect = OnecError("Request timeout")

        result, error = self.api.get_licenses_codes('CLIENT001')

        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn('Error communicating', error)
        self.assertIn('Request timeout', error)

    @patch('oc_cdtapi.OnecAPI.OnecAPI.get')
    def test_get_licenses_codes_empty_response(self, mock_get):
        """Test getting license codes with empty response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result, error = self.api.get_licenses_codes('CLIENT001')

        self.assertIsNone(error)
        self.assertEqual(result, [])

    def test_build_query_string_single_values(self):
        """Test query string builder with single values"""
        params = {'status': 'active', 'country': 'US', 'type': 'premium'}
        result = self.api._build_query_string(params)
        
        # Result should contain all parameters
        self.assertIn('status=active', result)
        self.assertIn('country=US', result)
        self.assertIn('type=premium', result)

    def test_build_query_string_with_lists(self):
        """Test query string builder with list values"""
        params = {'status': ['active', 'pending'], 'country': 'US'}
        result = self.api._build_query_string(params)
        
        self.assertIn('status=active', result)
        self.assertIn('status=pending', result)
        self.assertIn('country=US', result)

    def test_build_query_string_skip_empty_values(self):
        """Test query string builder skips empty values"""
        params = {'status': 'active', 'country': '', 'region': None, 'type': []}
        result = self.api._build_query_string(params)
        
        self.assertEqual(result, 'status=active')

    def test_build_query_string_numeric_values(self):
        """Test query string builder with numeric values"""
        params = {'status': 'active', 'count': 5, 'score': 3.14}
        result = self.api._build_query_string(params)
        
        self.assertIn('status=active', result)
        self.assertIn('count=5', result)
        self.assertIn('score=3.14', result)

    def test_build_license_query_params_under_limit(self):
        """Test license query params builder with clients under limit"""
        clients = ['CLIENT001', 'CLIENT002', 'CLIENT003']
        result = self.api._build_license_query_params(clients)
        
        self.assertEqual(result, 'CLIENT001|CLIENT002|CLIENT003')

    def test_build_license_query_params_at_limit(self):
        """Test license query params builder at exactly 100 clients"""
        clients = [f'CLIENT{i:03d}' for i in range(100)]
        result = self.api._build_license_query_params(clients)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.split('|')), 100)

    def test_build_license_query_params_over_limit(self):
        """Test license query params builder with clients over limit"""
        clients = [f'CLIENT{i:03d}' for i in range(101)]
        result = self.api._build_license_query_params(clients)
        
        self.assertIsNone(result)

    def test_build_license_query_params_none(self):
        """Test license query params builder with None"""
        result = self.api._build_license_query_params(None)
        
        self.assertIsNone(result)

    def test_build_license_query_params_empty_list(self):
        """Test license query params builder with empty list"""
        result = self.api._build_license_query_params([])
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()