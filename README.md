# octopus-oc-corelibs-cdtapi

## Core libraries consist of:

- *oc\_cdtapi* module
    - API.py — an extension to python requests for http/https quieries
    - Dbsm2API.py - an API to database schema manager (some propieritary implementations)
    - DevPIAPI.py — class dealing with Python Index
    — DmsAPI.py — an API to Distributive Management System (some propieritary implementations)
    - DmsGetverAPI.py — an API to GetVersion part of Distributive Management System (some propieritary implementations)
    - ForemanAPI.py — an API to Foreman (limited)
    - JenkinsAPI.py — an API to Jenkins v.1.x
    - NexusAPI.py — an API to Maven-compatible storage (currently Sonatype Nexus and JFrog Artifactory)
    - TestServer.py — Mock HTTP server for testing of API.py-based modules
    - nexus.py — command-line interface for Maven-compatible resources: upload, download, delete artifacts

- templates (for possible future use):
    - okd — template for Openshift OKD

Dockerfile builds bdist\_wheels for all libraries. Resulting image can be used to deploy to pypi or as a source to directly import libraries.
