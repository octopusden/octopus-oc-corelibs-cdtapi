This build requires three secrets to exist in the same project in OKD:

corelibs-bb-key — secret part of path to fire OKD build trigger
s-cdtcimanager — RSA private key to access bitbucket
s-art-cdt-builder — docker config.json with credentials to DOCKER\_REGISTRY\_HOST

