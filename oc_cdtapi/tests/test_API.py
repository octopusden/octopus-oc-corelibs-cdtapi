import unittest
import doctest
from .. import API

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(API))
    return tests

