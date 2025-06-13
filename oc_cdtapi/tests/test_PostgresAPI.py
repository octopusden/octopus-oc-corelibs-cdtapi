import unittest
from unittest.mock import patch, MagicMock
from oc_cdtapi.PgAPI import PostgresAPI

class TestPostgresAPI(unittest.TestCase):

    @patch('os.getenv')
    def setUp(self, mock_getenv):
        mock_getenv.return_value = 'dummy_token'
        self.api = PostgresAPI()

    @patch('oc_cdtapi.PgAPI.PostgresAPI.get')
    def test_get_deliveries(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'id': 1, 'gav': 'group:artifact:version', 'flag_approved': True},
            {'id': 2, 'gav': 'group:artifact:version', 'flag_approved': True}
        ]
        mock_get.return_value = mock_response

        request = {'gav': 'group:artifact:version', 'flag_approved': True}
        result = self.api.get_deliveries(request)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['gav'], 'group:artifact:version')
        mock_get.assert_called_once_with('rest/api/1/deliveries', params={'gav': 'group:artifact:version', 'flag_approved': True})

    @patch('oc_cdtapi.PgAPI.PostgresAPI.put')
    def test_update_delivery_by_gav(self, mock_put):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        gav = "com.example:artifact:1.0.0"
        update_data = {"status": "approved", "version": "1.0.1"}
        response = self.api.update_delivery_by_gav(gav, update_data)

        self.assertEqual(response.status_code, 200)
        mock_put.assert_called_once_with('rest/api/1/deliveries', json=update_data, params={"gav": "com.example:artifact:1.0.0"})

    @patch('oc_cdtapi.PgAPI.PostgresAPI.post')
    def test_post_historicaldelivery(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 12345, 'gav': 'com.example:artifact:1.0.0', 'status': 'delivered'}
        mock_post.return_value = mock_response

        new_delivery = {
            "gav": "com.example:artifact:1.0.0",
            "timestamp": "2023-04-01T12:00:00Z",
            "status": "delivered"
        }
        result = self.api.post_historicaldelivery(new_delivery)

        self.assertEqual(result.json()['id'], 12345)
        self.assertEqual(result.json()['gav'], 'com.example:artifact:1.0.0')
        mock_post.assert_called_once_with('rest/api/1/historicaldeliveries', json=new_delivery)

    @patch('oc_cdtapi.PgAPI.PostgresAPI.get')
    def test_get_task_by_id(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [{
          "id": 1,
          "status": "Completed",
          "hostname": "hostname",
          "action_code": "create",
          "commentary": "",
          "owner": "owner",
          "placement": 3,
          "project_code": "testproject",
          "task_content": {
            "hardware": {
              "memory_mb": 5120
            },
            "name": "hostname",
            "username": "username"
          },
          "jira_verification_ticket": "ticket_id",
          "status_desc": "There are more than 0 failures after the third Puppet report. Please check the host configuration",
          "creation_date": "2025-02-04 07:24:00"
        }]
        mock_get.return_value = mock_response

        result = self.api.get_task_by_id(1)

        self.assertEqual(result['id'], 1)
        self.assertEqual(result['hostname'], 'hostname')
        mock_get.assert_called_once_with('rest/api/1/tasks', params={"id": 1})

    @patch('oc_cdtapi.PgAPI.PostgresAPI.get')
    def test_get_task_by_id_and_username(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [{
          "id": 1,
          "status": "Completed",
          "hostname": "hostname",
          "action_code": "create",
          "commentary": "",
          "owner": "owner",
          "placement": 3,
          "project_code": "testproject",
          "task_content": {
            "hardware": {
              "memory_mb": 5120
            },
            "name": "hostname",
            "username": "username"
          },
          "jira_verification_ticket": "ticket_id",
          "status_desc": "There are more than 0 failures after the third Puppet report. Please check the host configuration",
          "creation_date": "2025-02-04 07:24:00"
        }]
        mock_get.return_value = mock_response

        result = self.api.get_task_by_id_and_username(1, "raprustandi")

        self.assertEqual(result['id'], 1)
        self.assertEqual(result['hostname'], 'hostname')
        mock_get.assert_called_once_with('rest/api/1/tasks', params={"id": 1, "username": "raprustandi"})

    @patch('oc_cdtapi.PgAPI.PostgresAPI.get')
    def test_get_task_custom_filter(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [{
          "id": 1,
          "status": "Completed",
          "hostname": "hostname",
          "action_code": "create",
          "commentary": "",
          "owner": "owner",
          "placement": 3,
          "project_code": "testproject",
          "task_content": {
            "hardware": {
              "memory_mb": 5120
            },
            "name": "hostname",
            "username": "username"
          },
          "jira_verification_ticket": "ticket_id",
          "status_desc": "There are more than 0 failures after the third Puppet report. Please check the host configuration",
          "creation_date": "2025-02-04 07:24:00"
        }]
        custom_filter = {"owner": "raprustandi"}
        mock_get.return_value = mock_response

        result = self.api.get_task_custom_filter(**custom_filter)

        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[0]['hostname'], 'hostname')
        mock_get.assert_called_once_with('rest/api/1/tasks', params=custom_filter)

    @patch('oc_cdtapi.PgAPI.PostgresAPI.post')
    def test_post_task(self, mock_post):
        inserted_task = {
          "status": "Completed",
          "action_code": "create",
          "commentary": "",
          "task_content": {
            "hardware": {
              "memory_mb": 5120
            },
            "name": "hostname",
            "username": "raprustandi"
          },
          "jira_verification_ticket": "ticket_id",
          "status_desc": "There are more than 0 failures after the third Puppet report. Please check the host configuration"
        }
        mock_post.return_value = None

        self.api.post_tasks(inserted_task)

        mock_post.assert_called_once_with('rest/api/1/tasks', json=inserted_task)

    @patch('oc_cdtapi.PgAPI.PostgresAPI.put')
    def test_update_task(self, mock_update):
        updated_task = {
          "status": "Building",
          "action_code": "create",
        }
        mock_update.return_value = None

        self.api.update_task(1, updated_task)

        mock_update.assert_called_once_with('rest/api/1/tasks/1', json=updated_task)

    @patch('oc_cdtapi.PgAPI.PostgresAPI.get')
    def test_get_client(self, mock_get):
        client_code = "_TEST_CLIENT"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "canReceive": True,
            "code": "_TEST_CLIENT",
            "country": "_Products",
            "isActive": True,
            "languageId": 1,
            "shouldEncrypt": True
        }
        mock_get.return_value = mock_response

        self.api.get_client_by_code(client_code)

        mock_get.assert_called_once_with(f'rest/api/1/clients/{client_code}')


if __name__ == '__main__':
    unittest.main()