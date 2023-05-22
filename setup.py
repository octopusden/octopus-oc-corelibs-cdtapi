#!/usr/bin/env python

from setuptools import setup
from sys import version_info

__version = "3.9.2"
install_requires = ["requests"]
tests_require = []

if version_info.major < 3:
    # these modlues comes with 3.6 and later intepreters but not included in 2.7
    install_requires.append("mock==2.0.0") # needed for tests only but can not be installed with 'pip' if not specified here
    install_requires.append("enum")

spec = {
    "name": "oc-cdtapi",
    "version": __version,
    "license": "Apache2.0",
    "description": "Custom Development python API libraries",
    "long_description": "",
    "long_description_content_type": "text/plain",
    "packages": ["oc_cdtapi"],
    "install_requires": install_requires,
    "tests_require": tests_require,
    "python_requires": ">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*",
    "scripts": [
        "nexus.py"
    ],
}


setup(**spec)
