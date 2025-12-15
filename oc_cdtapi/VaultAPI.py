import logging
import os
from typing import Any

import hvac
from hvac.exceptions import VaultError

# module level cache
_config_cache: dict[str, Any] = {}


class VaultAPI:
    def __init__(self,
                 vault_url=None,
                 vault_token=None,
                 vault_mount_point=None,
                 verify_ssl=True):
        self.vault_url = vault_url or os.getenv("VAULT_URL")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.mount_point = vault_mount_point or os.getenv("VAULT_MOUNT_POINT")
        self.verify_ssl = verify_ssl
        self._client = None

        # Create a logger instance for this class
        self.logger = logging.getLogger(__name__)

    @property
    def client(self):
        if self._client is None:
            if not self.vault_url:
                self.logger.warning("VAULT_URL environment variable or vault_url parameter is missing, skip using vault")
                return None
            if not self.vault_token:
                self.logger.warning("VAULT_TOKEN environment variable or vault_token parameter is missing, skip using vault")
                return None

            self._client = hvac.Client(
                url=self.vault_url,
                token=self.vault_token,
                verify=self.verify_ssl
            )

            if not self._client.is_authenticated():
                self.logger.warning("Failed to authenticate with Vault - check credentials, skip using vault")
                return None

        return self._client

    def parse_secret_name(self, name):
        if 'USER' in name:
            split_name = name.split('_USER')[0]
            return split_name, 'USER'

        if 'PASSWORD' in name:
            split_name = name.split('_PASSWORD')[0]
            return split_name, 'PASSWORD'

        return 'OTHER', name

    def get_secret_from_path(self, name):
        client = self.client
        if client is None:
            return None
        secret_path, credentials = self.parse_secret_name(name)
        try:
            response = client.secrets.kv.read_secret_version(path=secret_path, mount_point=self.mount_point)
            return response["data"]["data"].get(credentials)
        except VaultError as e:
            self.logger.warning(f"Failed getting data from vault for path {secret_path} and credentials {credentials}: {e}")
            return None

    def load_secret(self, key: str, defaults: dict[str, Any]) -> Any:
        def _get_value(key: str):
            if (value := self.get_secret_from_path(key=key)) is not None:
                return value
            for src in (os.environ, defaults):
                if (value := src.get(key)) is not None:
                    return value
            return None

        is_test = _get_value("PYTHON_ENV") == "test"
        key = f"{key}_TEST" if is_test else key
        if key not in _config_cache:
            _config_cache[key] = _get_value(key)
        return _config_cache[key]
