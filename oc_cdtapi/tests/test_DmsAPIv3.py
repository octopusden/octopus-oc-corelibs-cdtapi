import unittest
import unittest.mock
from ..DmsAPI import DmsAPIv3

class TestDmsApiV3(unittest.TestCase):
    def setUp(self):
        self._dms = DmsAPIv3(root="httsp://dms.example.com", user="test_user", auth="test_auth")
        self._dms.get = unittest.mock.MagicMock()

    def test_init(self):
        self.assertEqual(self._dms._env_prefix, "DMS")

    def test_ping(self):
        _ret = unittest.mock.MagicMock()
        _ret.content = 'test_content'
        self._dms.get.return_value = _ret
        self.assertEqual(self._dms.ping_dms(), _ret.content)
