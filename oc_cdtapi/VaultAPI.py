import logging
import os

import hvac
from hvac.exceptions import VaultError

class VaultAPI:
    def __init__(self,
                 vault_enable=False,
                 vault_url=None,
                 vault_token=None,
                 vault_mount_point=None,
                 verify_ssl=True):
        self.vault_enable = vault_enable or os.getenv("VAULT_ENABLE")
        self.vault_url = vault_url or os.getenv("VAULT_URL")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.mount_point = vault_mount_point or os.getenv("VAULT_MOUNT_POINT")
        self.use_staging_secrets = os.getenv("USE_STAGING_ENVIRONMENT", "false").lower() == "true" #Check whether we have env USE_STAGING_ENVIRONMENT true or not
        self.verify_ssl = verify_ssl
        self._client = None

    @property
    def client(self):
        if not self.vault_enable:
            logging.warning("VAULT_ENABLE environment set to false, skip using vault")
            return None

        if self._client is None:
            if not self.vault_url:
                logging.warning("VAULT_URL environment variable or vault_url parameter is missing, skip using vault")
                return None
            if not self.vault_token:
                logging.warning("VAULT_TOKEN environment variable or vault_token parameter is missing, skip using vault")
                return None

            self._client = hvac.Client(
                url=self.vault_url,
                token=self.vault_token,
                verify=self.verify_ssl
            )

            if not self._client.is_authenticated():
                logging.warning("Failed to authenticate with Vault - check credentials, skip using vault")
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
        if self.use_staging_secrets:
            secret_path = secret_path + "_TEST"

        try:
            response = client.secrets.kv.read_secret_version(path=secret_path, mount_point=self.mount_point)
            return response['data']['data'].get(credentials)
        except VaultError as e:
            logging.warning(f"Failed getting data from vault for path {secret_path} and credentials {credentials}: {e}")
            return None

    def load_secret(self, name, default=None):
        return self.get_secret_from_path(name) or os.getenv(name, default)