#!/usr/bin/env python

from setuptools import setup

__version = "3.20.0"

install_requires = [
    "requests",
    "packaging",
    "psycopg2-binary"
]
tests_require = []

spec = {
    "name": "oc-cdtapi",
    "version": __version,
    "license": "Apache2.0",
    "description": "Custom Development python API libraries",
    "long_description": "Custom Development python API libraries",
    "long_description_content_type": "text/plain",
    "packages": ["oc_cdtapi"],
    "install_requires": install_requires,
    "tests_require": tests_require,
    "python_requires": ">=3.6",
    "scripts": [
        "nexus.py"
    ],
}


setup(**spec)
