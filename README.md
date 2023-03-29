# octopus-corelibs-oc\_cdtapi

## Core libraries consist of:

- API.py — an extension to python requests
- DevPIAPI.py — class dealing with Python Index
— DmsAPI.py — an api to dms
- DmsGetverAPI.py — an api to dms get version
- ForemanAPI.py — an api to foreman
- JenkinsAPI.py — an api to jenkins
- NexusAPI.py — an api to nexus / artifactory
- TestServer.py — mock http server for testing of API.py based modules
- nexus.py — cli dealing with nexus / artifactory. Upload, download, delete artifacts
- okd — template for openshift OKD

Dockerfile builds bdist\_wheels for all libraries. Resulting image can be used to deploy to pypi or as a source to directly import libraries.
