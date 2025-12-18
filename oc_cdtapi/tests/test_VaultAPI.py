import requests
import unittest
from unittest.mock import patch, MagicMock
from oc_cdtapi.VaultAPI import VaultAPI


class TestVaultAPI(unittest.TestCase):
    @patch('os.getenv')
    def setUp(self, mock_getenv):
        mock_getenv.side_effect = lambda key, default=None: {
            "VAULT_ENABLE": "true",
            "VAULT_URL": "http://127.0.0.1:8200",
            "VAULT_TOKEN": "dummy_token",
            "VAULT_PATH": "secret/data/myapp",
            "VAULT_MOUNT_POINT": "secret",
            "USE_STAGING_ENVIRONMENT": "false"
        }.get(key, default)

        self.vault = VaultAPI()

    @patch('oc_cdtapi.VaultAPI.hvac.Client')
    def test_client_authenticated(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        client = self.vault.client
        self.assertIsNotNone(client)
        mock_client_class.assert_called_once_with(
            url="http://127.0.0.1:8200",
            token="dummy_token",
            verify=True
        )

    @patch('oc_cdtapi.VaultAPI.hvac.Client')
    def test_client_not_authenticated(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = False
        mock_client_class.return_value = mock_client

        client = self.vault.client
        self.assertIsNone(client)

    @patch('oc_cdtapi.VaultAPI.hvac.Client')
    def test_get_secret_from_path(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.read_secret_version.return_value = {
            'data': {'data': {'DB_PASSWORD': 'test_pass'}}
        }
        mock_client_class.return_value = mock_client

        result = self.vault.load_secret("PSQL__DB_PASSWORD")
        self.assertEqual(result, "test_pass")

        mock_client.secrets.kv.read_secret_version.assert_called_once_with(
            path="PSQL",
            mount_point="secret"
        )

    @patch('oc_cdtapi.VaultAPI.hvac.Client')
    def test_get_secret_from_path_should_return_none_on_invalid_name(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.read_secret_version.return_value = {
            'data': {'data': {'PASSWORD': 'test_pass'}}
        }
        mock_client_class.return_value = mock_client

        result = self.vault.load_secret("PSQL_PASSWORD")
        self.assertEqual(result, None)
    
    @patch.dict('os.environ', {'PYTHON_ENV': 'test'})
    @patch('oc_cdtapi.VaultAPI.hvac.Client')
    def test_load_secret_should_read_test_secrets(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.read_secret_version.return_value = {
            'data': {'data': {'DB_PASSWORD_TEST': 'test_pass1'}}
        }
        mock_client_class.return_value = mock_client

        result = self.vault.load_secret("PSQL__DB_PASSWORD")
        self.assertEqual(result, "test_pass1")
    
    @patch.dict('os.environ', {'PSQL__DB_PASSWORD': 'test_pass2'})
    @patch('oc_cdtapi.VaultAPI.hvac.Client')
    def test_load_secret_should_read_secret_from_hv_first(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.read_secret_version.return_value = {
            'data': {'data': {'DB_PASSWORD': 'test_pass1'}}
        }
        mock_client_class.return_value = mock_client

        result = self.vault.load_secret("PSQL__DB_PASSWORD", default="test_pass3")
        self.assertEqual(result, "test_pass1")


    @patch.dict('os.environ', {'PSQL__DB_PASSWORD': 'test_pass2'})
    @patch('oc_cdtapi.VaultAPI.hvac.Client')
    def test_load_secret_should_read_secret_from_env_when_no_secret_in_hv(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.read_secret_version.return_value = {
            'data': {'data': {}}
        }
        mock_client_class.return_value = mock_client
        result = self.vault.load_secret(
            "PSQL__DB_PASSWORD",
            default="test_pass3"
        )
        self.assertEqual(result, "test_pass2")

    @patch.dict('os.environ', {'PSQL__DB_PASSWORD': 'test_pass2'})
    def test_load_secret_should_read_secret_from_env_when_hv_is_not_present(self):
        vault = VaultAPI()
        result = vault.load_secret(
            "PSQL__DB_PASSWORD",
            default="test_pass3"
        )
        self.assertEqual(result, "test_pass2")

    def test_load_secret_should_read_secret_from_defaults_when_hv_and_env_is_not_present(self):
        vault = VaultAPI()
        result = vault.load_secret("PSQL__DB_PASSWORD", default="test_pass3")
        self.assertEqual(result, "test_pass3")

    def test_load_secret_should_return_none_when_secret_is_not_found(self):
        vault = VaultAPI()
        result = vault.load_secret("PSQL__DB_PASSWORD")
        self.assertEqual(result, None)

    @patch('oc_cdtapi.VaultAPI.hvac.Client')
    def test_load_secret_should_read_secret_when_hv_is_present_but_unavailable(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.is_authenticated.side_effect = requests.exceptions.ConnectionError()
        mock_client.secrets.kv.read_secret_version.side_effect = requests.exceptions.ConnectionError()
        mock_client_class.return_value = mock_client
        result = self.vault.load_secret("PSQL__DB_PASSWORD", default="test_pass3")
        self.assertEqual(result, "test_pass3")  
