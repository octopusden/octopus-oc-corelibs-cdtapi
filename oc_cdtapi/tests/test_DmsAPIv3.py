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
        self._dms.get.assert_called_once()

    def test_get_components(self):
        _ret_dict = {"components": ["component"]}
        _ret = unittest.mock.MagicMock()
        _ret.json = unittest.mock.MagicMock(return_value=_ret_dict)
        self._dms.get.return_value = _ret
        self.assertListEqual(_ret_dict.get("components"), self._dms.get_components())
        self._dms.get.assert_called_once_with('components')

    def test_get_versions(self):
        _ret_dict = {"versions": [
            {"version": "1", "status": "RELEASE"},
            {"version": "2", "status": "RC"},
            {"version": "3", "status": "RELEASE"}]}
        _ret = unittest.mock.MagicMock()
        _ret.json = unittest.mock.MagicMock(return_value=_ret_dict)
        self._dms.get.return_value = _ret
        self.assertListEqual(["1", "2", "3"], self._dms.get_versions('component', version_status=None))
        self._dms.get.assert_called_once_with(['components', 'component', 'versions'])

        # getting RC
        self._dms.get.reset_mock()
        self.assertListEqual(["2"], self._dms.get_versions('component', version_status="RC"))
        self._dms.get.assert_called_once_with(['components', 'component', 'versions'])

        # getting RELEASE
        self._dms.get.reset_mock()
        self.assertListEqual(["1", "3"], self._dms.get_versions('component'))
        self._dms.get.assert_called_once_with(['components', 'component', 'versions'])

    def test_get_artifacts(self):
        _ret_dict = {"artifacts": ["1", "2", "3"]}
        _ret = unittest.mock.MagicMock()
        _ret.json = unittest.mock.MagicMock(return_value=_ret_dict)
        self._dms.get.return_value = _ret
        self.assertListEqual(["1", "2", "3"], self._dms.get_artifacts('component', "version"))
        self._dms.get.assert_called_once_with(["components", "component", "versions", "version", "artifacts"],
                                              params=None)
        self._dms.get.reset_mock()
        self.assertListEqual(["1", "2", "3"], self._dms.get_artifacts('component', "version", "type"))
        self._dms.get.assert_called_once_with(["components", "component", "versions", "version", "artifacts"],
                                              params={"type": "type"})

    def test_download_artifact(self):
        _ret = "test_content"
        self._dms.get.return_value = _ret
        self.assertEqual(_ret, self._dms.download_artifact(1, write_to='tempfile'))
        self._dms.get.assert_called_once_with(["artifacts", "1", "download"], stream=True, write_to="tempfile")

    def test_download_component(self):
        _ret = "test_content"
        self._dms.get.return_value = _ret
        self.assertEqual(_ret, self._dms.download_component("component", "version", 1, write_to='tempfile'))
        self._dms.get.assert_called_once_with([
            "components", "component", "versions", "version", "artifacts", "1", "download"],
                                              stream=True, write_to="tempfile")

    def test_get_artifact_info(self):
        _ret = unittest.mock.MagicMock()
        self._dms.get.return_value = _ret
        self._dms.get_artifact_info("component", "version", 1)
        self._dms.get.assert_called_once_with([
            "components", "component", "versions", "version", "artifacts", "1"])
        _ret.json.assert_called_once()
            
