import re
import logging
import os
from typing import Any, List, Optional

import hvac
import requests
from hvac.exceptions import VaultError

SECRET_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*__[A-Z][A-Z0-9_]*$")


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
    def client(self) -> Optional[hvac.Client]:
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
            try:
                is_authenticated = self._client.is_authenticated()
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Failed to authenticate with Vault - Vault is unreachable: {e}")
                self._client = None
                return None
            if not is_authenticated:
                self.logger.warning("Failed to authenticate with Vault - check credentials, skip using vault")
                self._client = None
                return None
        return self._client

    def _parse_secret_name(self, name: str) -> List[str]:
        if not SECRET_PATTERN.match(name):
            raise ValueError("Secret name must match <PATH>__<KEY>")

        return name.split("__", 1)

    def get_secret_from_path(self, name: str) -> Optional[Any]:
        client = self.client
        if client is None:
            return None
        try:
            secret_path, credentials = self._parse_secret_name(name=name)
        except ValueError as e:
            self.logger.warning(f"Failed parsing secret: {e}")
            return None

        try:
            response = client.secrets.kv.read_secret_version(path=secret_path, mount_point=self.mount_point)
            return response["data"]["data"].get(credentials)
        except VaultError as e:
            self.logger.warning(f"Failed getting data from vault for path {secret_path} and credentials {credentials}: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.warning(f"Failed to retrieve secret from Vault - Vault is unreachable: {e}")
            return None

    def load_secret(self, name: str, default: Optional[Any] = None) -> Optional[Any]:
        is_test = os.getenv("PYTHON_ENV") == "test"
        if is_test:
            name = f"{name}_TEST"

        value = os.getenv(name)
        if value is not None:
            return value

        value = self.get_secret_from_path(name=name)
        if value is None:
            return default
        return value
