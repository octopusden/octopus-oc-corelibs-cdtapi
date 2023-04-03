import sys
import io
import tempfile
import os

from unittest import TestCase
from nexus import ArtifactTool
from oc_cdtapi.NexusAPI import parse_gav


class MockAPI():
    """
    Mocked NexusAPI class for testing purposes
    """

    def check_gav(self, gav):
        try:
            parse_gav(gav)
        except ValueError:
            return False
        else:
            return True

    def info(self, gav, repo=None):
        if not self.check_gav(gav):
            raise ValueError("Incorrect GAV was provided")

    def ls(self, gav, repo=None):
        pass

    def exists(self, gav, repo=None):
        ex = self.check_gav(gav)
        return ex

    def cat(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        res = "<Response [204]>"
        return res

    def update_metadata(self, *args, **kwargs):
        pass

    def upload(self, gav, data=None, metadata=None, repo=None):
        if not repo:
            raise ValueError("You must provide repo name")
        res = "<Response [201]>"
        return res

    @property
    def repo_default(self):
        return "default"

    def gav_get_url(self, gav, repo=None):
        return "default_url"

    def remove(self, gav, repo=None):
        if not repo:
            raise SystemExit(1)

        if sys.version_info.major >= 3:
            return "'%s' has been deleted" % gav

        return unicode("'%s' has been deleted" % gav)

class ArtifactToolTestSuite(TestCase):

    def setUp(self):
        self.conn = ArtifactTool(testing=True)
        self.conn.API = MockAPI()
        self.cout = io.StringIO()
        sys.stdout = self.cout
        self.tempfile = tempfile.NamedTemporaryFile(delete=True)
        os.environ["MVN_UPLOAD_REPO"] = ""

    def tearDown(self):
        self.tempfile.close()

    def test_no_gav_provided(self):
        with self.assertRaises(ValueError):
            self.conn.download_artifact(None)
            self.conn.delete_artifact(None)
            self.conn.upload_artifact(None)
            self.conn.get_info(None)

    def test_get_info_multiple_gavs(self):
        self.conn.get_info(["GG:AA:VV", "GG1:AA1:VV1"])
        if sys.version_info.major == 2:
            self.assertRegexpMatches(self.cout.getvalue(), "GG:AA:VV")
        else:
            self.assertRegex(self.cout.getvalue(), "GG:AA:VV")

    def test_check_existence_correct_gav(self):
        self.assertTrue(self.conn.check_existence("GG:AA:VV"))

    def test_download_artifact_no_path_provided(self):
        self.conn.download_artifact(["GG:AA:VV"])
        _check_msg = "Downloaded: 'GG:AA:VV'"
        if sys.version_info.major == 2:
            self.assertRegexpMatches(self.cout.getvalue(), _check_msg)
        else:
            self.assertRegex(self.cout.getvalue(), _check_msg)

    def test_download_artifact_not_dir_in_path(self):
        with self.assertRaises(ValueError):
            self.conn.download_artifact(["GG:AA:VV"], self.tempfile.name)

    def test_download_artifact_multiple_gavs(self):
        _list = ["GG:AA:VV", "GG1:AA1:VV1"]
        self.conn.download_artifact(_list, ".")

        if sys.version_info.major == 2:
            _check_mthd = self.assertRegexpMatches
        else:
            _check_mthd = self.assertRegex

        for _art in _list:
            _check_mthd(self.cout.getvalue(), "Downloaded: '%s'" % _art)

    def test_download_artifact_filename_provided(self):
        self.conn.download_artifact(["GG:AA:VV"], result_filenames=["test_file.zip"])
        if sys.version_info.major == 2:
            self.assertRegexpMatches(self.cout.getvalue(), "test_file.zip")
        else:
            self.assertRegex(self.cout.getvalue(), "test_file.zip")

    def test_download_artifact_gavs_filenames_quantity_mismatch(self):
        with self.assertRaises(ValueError):
            self.conn.download_artifact(["GG:AA:VV","GG1:AA1:VV1"], result_filenames=["test_file.zip"])

    def test_download_artifact_multiple_gavs_filenames(self):
        _arts = {"GG:AA:VV": "test_file1.zip", "GG1:AA1:VV1": "test_file2.zip"}
        self.conn.download_artifact(list(_arts.keys()), result_filenames=list(_arts.values()))

        if sys.version_info.major == 2:
            _check_mthd = self.assertRegexpMatches
        else:
            _check_mthd = self.assertRegex

        for _art, _file in _arts.items():
            _check_mthd(self.cout.getvalue(), "Downloaded: '%s' ==> '%s'" % (_art, _file))

    def test_delete_artifact_no_upload_repo(self):
        with self.assertRaises(SystemExit) as ec: 
            self.conn.delete_artifact(["GG:AA:VV", "GG1:AA1:VV1"])
        exit = ec.exception
        self.assertEqual(exit.code, 1)

    def test_delete_artifact_multiple_gavs(self):
        self.conn.delete_artifact(["GG:AA:VV", "GG1:AA1:VV1"], "test")
        if sys.version_info.major == 2:
            self.assertRegexpMatches(self.cout.getvalue(), "has been deleted")
        else:
            self.assertRegex(self.cout.getvalue(), "has been deleted")

    def test_upload_artifact_incorrect_file(self):
        with self.assertRaises(ValueError):
            self.conn.upload_artifact(["GG:AA:VV"], None, "test")

    def test_upload_artifact_no_upload_repo(self):
        with self.assertRaises(ValueError) as ec:
            self.conn.upload_artifact(["GG:AA:VV"], self.tempfile.name, None)

    def test_upload_artifact_multiple_gavs(self):
        _list = ["GG:AA:VV", "GG1:AA1:VV1"]
        self.conn.upload_artifact(_list, self.tempfile.name, "test")
        
        if sys.version_info.major == 2:
            _assert = self.assertRegexpMatches
        else:
            _assert = self.assertRegex

        _assert(self.cout.getvalue(), "^Uploaded: .* ==> '%s'$" % _list.pop(0))
