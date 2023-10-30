#!/usr/bin/env python3

import unittest
import unittest.mock
from ..RundeckAPI import RundeckAPI

class TestRundeckApi(unittest.TestCase):
    def setUp(self):
        self._rundeck = RundeckAPI(url="https://rundeck.example.com", user="test_user", password="test_auth")
        self._rundeck.get = unittest.mock.MagicMock()
        self._rundeck.post = unittest.mock.MagicMock()
        self._rundeck.put = unittest.mock.MagicMock()
        self._rundeck.delete = unittest.mock.MagicMock()

    def test_init(self):
        self.assertEqual(self._rundeck.root, "https://rundeck.example.com")
