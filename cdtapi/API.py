# requires python-requests rpm package
import doctest
import os
import shutil  # this required to copy data between file objects
import posixpath

import requests

import sys

if sys.version_info.major == 2:
    strtype = basestring
elif sys.version_info.major == 3:
    strtype = str

class HttpAPIError(Exception):

    def __init__(self, code=0, url='', resp=None, text=''):
        self.code = code
        self.url = url
        self.resp = resp
        self.text = text


    def __str__(self):
        return self.text + ': Code ' + str(self.code) + ' ' + self.url


class HttpAPI(object):
    """ Base class for implementing HTTP API """
    # This attributes may be re-defined in your child classes
    _error = HttpAPIError  # Error to throw if something goes wrong
    raise_exception_low = 200  # Rise exception if return code is < 200
    raise_exception_high = 399  # Raise exception if return code is > 399
    _env_prefix = None  # If set, we read prefix_USER, prefix_PASSWORD and prefix_URL
    # if root, user and auth was not provided to class constructor
    _env_url = '_URL'
    _env_user = '_USER'
    _env_auth = '_PASSWORD'

    def __init__(self, root=None, user=None, auth=None, readonly=False, anonymous=False):
        """
        :param root: Root URL (uses *_URL by default)
        :param user: Username (uses *_USER by default)
        :param auth: Password (uses *_PASSWORD by default)
        :param readonly: sets readonly property, should be explictly supported by child 
        :param anonymous: ignore username/password provided and use anonymous requests

        >>> import os
        >>> from cdtapi.API import HttpAPI
        >>> def test(port):
        ...     HttpAPI._env_prefix='HTTP'
        ...     os.environ['HTTP_URL'] = 'http://127.0.0.1:' + str(port)
        ...     api = HttpAPI()
        ...     api.get('testinit')
        ...
        >>> from cdtapi.TestServer import test_wrapper
        >>> test_wrapper(test)
        "GET /testinit HTTP/1.1" 200 -
        >>> os.environ[ 'HTTP_URL' ] = "https://127.0.0.1/";
        >>> HttpAPI._env_prefix = 'HTTP';
        >>> obj_api = HttpAPI();
        >>> obj_api.root
        'https://127.0.0.1/'
        >>> obj_api.web.verify
        False
        """

        self.readonly = readonly
        if self._env_prefix != None:
            if not root: root = os.getenv(self._env_prefix + self._env_url)
            if not user: user = os.getenv(self._env_prefix + self._env_user)
            if not auth: auth = os.getenv(self._env_prefix + self._env_auth)
        if not root: raise ValueError('Server URL for service [%s] not set' % self._env_prefix)
        self.root = root
        self.web = requests.Session()
        if user != None and not anonymous: self.web.auth = (user, auth)

        if self.root.startswith( "https:" ):
            self.web.verify = False;


    def set_readonly(self, readonly=True):
        self.readonly = readonly


    def re(self, req):
        """ Constructs request URL from request name """
        return posixpath.join(self.root, req)


    def pp(self, resp, write_to=None, stream=False, **kvarg):
        """ Post-processes response

        New feature! If write_to parameter is given to any method, that returns response
        object, request result will be written to fd or filename specified in write_to.

        If stream == True, file will be written on the fly, without reading all the data

        >>> import sys
        >>> import io
        >>> class FakeResp(object):
        ...     raw = io.BytesIO(b'Read data')
        ...     content = b'Read data!'
        ...     status_code = 200
        ...
        >>> api = HttpAPI('http://127.0.0.1')
        >>> fake_resp = FakeResp()
        >>> read_fd = io.BytesIO()
        >>> r = api.pp(fake_resp, stream = True, write_to = read_fd)
        >>> r == fake_resp
        True
        >>> if sys.version_info.major == 2:
        ...     value = read_fd.getvalue()
        ... else:
        ...     value = read_fd.getvalue().decode()
        >>> value
        'Read data'
        >>> read_fd = io.BytesIO()
        >>> r = api.pp(fake_resp, stream = False, write_to = read_fd)
        >>> r == fake_resp
        True
        >>> if sys.version_info.major == 2:
        ...     value = read_fd.getvalue()
        ... else:
        ...     value = read_fd.getvalue().decode()
        >>> value
        'Read data!'
        >>> fake_resp.raw = io.BytesIO(b'Read data2')
        >>> import tempfile
        >>> tmpfile = tempfile.mktemp()
        >>> if os.path.exists(tmpfile): os.unlink(tmpfile)
        >>> r = api.pp(fake_resp, stream = True, write_to = tmpfile)
        >>> r == fake_resp
        True
        >>> open(tmpfile, 'r').read()
        'Read data2'
        >>> os.unlink(tmpfile)
        >>> r = api.pp(fake_resp, stream = False, write_to = tmpfile)
        >>> r == fake_resp
        True
        >>> open(tmpfile, 'r').read()
        'Read data!'
        >>> os.unlink(tmpfile)

        """

        if resp.status_code < self.raise_exception_low or resp.status_code > self.raise_exception_high:
            raise self._error(resp.status_code, resp.url, resp, 'Error making request to server')
        if write_to != None:
            if isinstance (write_to, strtype):
                fd = open(write_to, 'wb')
            else:
                fd = write_to
            if not stream:
                fd.write(resp.content)
            else:
                shutil.copyfileobj(resp.raw, fd)
            fd.flush()
            if isinstance (write_to, strtype): fd.close()
            del fd
        return resp


    def __kvarg(self, kvarg):
        kvarg = kvarg.copy()
        if 'write_to' in kvarg: del kvarg['write_to']
        return kvarg


    def get(self, req, params=None, files=None, data=None, headers=None, **kvarg):
        """Sends GET request

        >>> def test(port):
        ...     api = HttpAPI('http://127.0.0.1:' + str(port))
        ...     api.get('getrequest')
        ...
        >>> from cdtapi.TestServer import test_wrapper
        >>> test_wrapper(test)
        "GET /getrequest HTTP/1.1" 200 -

        >>> import io
        >>> def test(port):
        ...     api = HttpAPI('http://127.0.0.1:' + str(port))
        ...     bio = io.BytesIO()
        ...     api.get('getrequest', write_to = bio)
        ...     if bio.getvalue() == b'hello, world!': exit(0)
        ...     exit(123)
        ...
        >>> test_wrapper(test, data = 'hello, world!', ret = True)
        "GET /getrequest HTTP/1.1" 200 -
        0

        """

        resp = self.web.get(self.re(req), params=params, data=data, files=files, headers=headers, **self.__kvarg(kvarg))
        return self.pp(resp, **kvarg)


    def post(self, req, params=None, files=None, data=None, headers=None, **kvarg):
        """Sends POST request"""
        resp = self.web.post(self.re(req), params=params, data=data, files=files, headers=headers, **kvarg)
        return self.pp(resp, **kvarg)


    def put(self, req, params=None, files=None, data=None, headers=None, **kvarg):
        """Sends PUT request
        >>> def test(port):
        ...     api = HttpAPI('http://127.0.0.1:' + str(port))
        ...     api.put('getrequest')
        ...
        >>> from cdtapi.TestServer import test_wrapper
        >>> test_wrapper(test)
        "PUT /getrequest HTTP/1.1" 200 -

        """

        resp = self.web.put(self.re(req), params=params, data=data, files=files, headers=headers, **kvarg)
        return self.pp(resp, **kvarg)


    def delete(self, req, params=None, files=None, data=None, headers=None, **kvarg):
        """Sends DELETE request"""
        resp = self.web.delete(self.re(req), params=params, data=data, files=files, headers=headers, **kvarg)
        return self.pp(resp, **kvarg)

    def head(self, req, params=None, files=None, data=None, headers=None, **kvarg):
        """Sends HEAD request"""
        resp = self.web.head(self.re(req), params=params, data=data, files=files, headers=headers, **kvarg)
        return self.pp(resp, **kvarg)


# Two shortcuts to deal with XML without having full XML support
def get_xml_tag(config, tag):
    """Gets tag value from xml config"""
    return ((config.split('<' + tag + '>')[1]).split('</' + tag + '>')[0])


def edit_xml_tag(config, tag, value):
    """Sets tag value in xml config. Works fine if there is only single such tag in XML"""
    config = config.split('<' + tag + '>')[0] + '<' + tag + '>' + value + '</' + tag + '>' + \
             config.split('</' + tag + '>')[1]
    return config


if __name__ == "__main__":
    import doctest

    doctest.testmod()
