
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.sync_bitrix_keycloak import (
    KeycloakAdminClient,
    load_mapping,
    main,
)


class TestSyncBitrixKeycloak(unittest.TestCase):
    def test_load_mapping(self):
        mapping_path = Path("elms/elms/sso/data/email-mapping.csv")
        mapping = load_mapping(mapping_path)
        self.assertIn("274", mapping)
        erokhin = mapping["274"]
        self.assertEqual(erokhin["bitrix_email"], "aeroalgo@gmail.com")
        self.assertEqual(erokhin["yandex_email"], "erokhin.a@nftgz.ru")
        self.assertIn("admin", erokhin["keycloak_roles"])

    def test_dry_run_execution(self):
        with patch.dict("os.environ", {}, clear=True):
            exit_code = main(["--dry-run"])
            self.assertEqual(exit_code, 0)

    def test_keycloak_admin_client_methods(self):
        client = KeycloakAdminClient("http://localhost:8480", "elms")
        client.token = "fake-token"

        with patch.object(client, "_api_request", return_value=[{"id": "user-123", "email": "test@nftgz.ru"}]):
            found = client.find_user_by_email("test@nftgz.ru")
            self.assertIsNotNone(found)
            self.assertEqual(found["id"], "user-123")

        with patch.object(client, "_api_request", return_value={}):
            client.update_user("user-123", {"enabled": True})


if __name__ == "__main__":
    unittest.main()
