# This module contains little test HTTP server for checking HTTP API based modules

import sys
from multiprocessing import Process
from requests import Session
import doctest

if sys.version_info.major == 3:
    from http.server import HTTPServer, BaseHTTPRequestHandler
else:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

class HTTPRequestHandler(BaseHTTPRequestHandler):

    def process(self,tpy):
        self.send_response(self.server.ret_code)
        if self.server.data_headers:
            for header in self.server.data_headers:
                self.send_header(header)
        self.end_headers()
        if 'data_to_send' in self.server.__dict__ and self.server.data_to_send:
            dts = self.server.data_to_send
            if sys.version_info.major == 3:
                dts = bytes (dts, 'UTF-8')
            self.wfile.write (dts)


    def do_PUT(self):
        self.process('PUT')


    def do_GET(self):
        self.process('GET')


    def do_POST(self):
        self.process('POST')


    def do_DELETE(self):
        self.process('DELETE')

    def do_HEAD(self):
        self.process('HEAD')


    def log_message(self,fmt, *args):
        print((fmt % args))



def test_server(port, rc = 200, data = None, headers = []):
    srv = HTTPServer(('127.0.0.1',port),HTTPRequestHandler)
    srv.ret_code = rc
    srv.data_to_send = data
    srv.data_headers = headers
    return srv


def test_function(port, request='', code = 0, data_to_expect = None):
    resp = Session().get('http://127.0.0.1:' + str(port) + request)
    if data_to_expect:
        received = resp.content.decode('UTF-8')
        if received != data_to_expect: exit(254)
    exit(code)


def test_wrapper(func = test_function, num_requests = 1, rc=200, ret=False, data=None, headers=None, *args, **kvargs):
    """
    >>> from TestServer import test_wrapper
    >>> test_wrapper()
    "GET / HTTP/1.1" 200 -
    >>> test_wrapper(rc=307)
    "GET / HTTP/1.1" 307 -
    >>> test_wrapper(rc=404, ret = True, code=112)
    "GET / HTTP/1.1" 404 -
    112
    >>> test_wrapper(ret = True, data_to_expect = 'hello', data = 'hello')
    "GET / HTTP/1.1" 200 -
    0
    >>> test_wrapper(ret = True, data_to_expect = 'hello', data = 'hi')
    "GET / HTTP/1.1" 200 -
    254
    """

    if not 'port' in kvargs: kvargs['port'] = 65111
    srv = test_server(kvargs['port'], rc, data, headers)
    proc = Process(group=None, target=func, name=None, args=args, kwargs=kvargs)
    proc.daemon = 1
    proc.start()
    for req in range(0, num_requests): srv.handle_request()
    proc.join(5)
    del srv
    if ret: return proc.exitcode


if __name__ == "__main__":
    import doctest
    doctest.testmod()



