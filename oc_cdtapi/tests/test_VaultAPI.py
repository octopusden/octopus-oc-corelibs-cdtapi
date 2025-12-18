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
            'data': {'data': {'PASSWORD': 's3cr3t'}}
        }
        mock_client_class.return_value = mock_client

        result = self.vault.load_secret("DB_PASSWORD")
        self.assertEqual(result, "s3cr3t")

        mock_client.secrets.kv.read_secret_version.assert_called_once_with(
            path="DB",
            mount_point="secret"
        )

    @patch('os.getenv')
    def test_load_secret_fallback_env(self, mock_getenv):
        mock_getenv.side_effect = lambda key, default=None: ("success_get_data_from_env" if key == "DB_USER" else default)
        vault = VaultAPI(vault_enable=False)

        result = vault.load_secret("DB_USER")
        self.assertEqual(result, "success_get_data_from_env")
