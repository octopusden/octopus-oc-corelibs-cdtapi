from setuptools import setup, find_packages
import unittest
from doctest import DocFileSuite
import os
from sys import version_info
from datetime import datetime

def dynamic_version(str_version):
    """
    Returns full version of a package
    :param str_version: string, package version to append
    :return: str_version with appended build_id
    """

    str_vfile = 'version.txt'

    if not os.path.exists(str_vfile):
        fl_out = open(str_vfile, 'w')
        fl_out.write(datetime.strftime(datetime.now(), "%Y%m%d%H%M%S"))
        fl_out.close()

    fl_in = open(str_vfile)
    str_bid = fl_in.read().strip()
    fl_in.close()

    return '.'.join([str_version, str_bid])


MAJOR = 3
MINOR = 8 
RELEASE = 1

install_requires = ["requests", "mock"]
tests_require = []

if version_info.major == 2:
    install_requires.append("enum")
    tests_require.append("mock==2.0.0")

spec = {
    "name": "oc_cdtapi",
    "version": dynamic_version('.'.join(list(map(lambda x: str(x), [MAJOR, MINOR, RELEASE])))),
    "license": "Apache2.0",
    "description": "Custom Development python API libraries",
    "packages": find_packages(),
    "install_requires": install_requires,
    "tests_require": tests_require,
    "scripts": [
        "nexus.py"
    ],

}

setup(**spec)
