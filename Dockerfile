ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION}

COPY . /local/cdtapi

WORKDIR /local/cdtapi

RUN python setup.py sdist bdist_wheel && python -m pip install dist/*.whl && python setup.py test

