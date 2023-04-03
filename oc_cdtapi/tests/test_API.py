import unittest
import doctest
import oc_cdtapi.API

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(oc_cdtapi.API))
    return tests

