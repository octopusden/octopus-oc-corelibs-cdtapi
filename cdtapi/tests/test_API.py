import unittest
import doctest
import cdtapi.API

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(cdtapi.API))
    return tests

