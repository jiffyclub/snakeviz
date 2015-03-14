"""
This module contains the command line interface for snakeviz.

"""
from __future__ import print_function

import optparse
import os
import random
import socket
import sys
import threading
import webbrowser

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus


# As seen in IPython:
# https://github.com/ipython/ipython/blob/8be7f9abd97eafb493817371d70101d28640919c/IPython/html/notebookapp.py
# See the IPython license at:
# https://github.com/ipython/ipython/blob/master/COPYING.rst.
def random_ports(port, n):
    """Generate a list of n random ports near the given port.
    The first 5 ports will be sequential, and the remaining n-5 will be
    randomly selected in the range [port-2*n, port+2*n].
    """
    for i in range(min(5, n)):
        yield port + i
    for i in range(n-5):
        yield max(1, port + random.randint(-2*n, 2*n))


def main(argv=sys.argv[1:]):
    parser = optparse.OptionParser(
        usage='%prog [options] filename'
    )
    parser.add_option('-H', '--hostname', metavar='ADDR', default='127.0.0.1',
                      help='hostname to bind to (default: 127.0.0.1')

    parser.add_option('-p', '--port', type='int', metavar='PORT', default=8080,
                      help='port to bind to; if this port is already in use a '
                           'free port will be selected automatically '
                           '(default: %default)')

    parser.add_option('-b', '--browser', metavar='PATH',
                      help='name of webbrowser to launch as described in '
                           'the documentation of Python\'s webbrowser module: '
                           'https://docs.python.org/3/library/webbrowser.html')

    parser.add_option('-s', '--server', action="store_true", dest="server",
                      default=False,
                      help='start SnakeViz in server-only mode--'
                           'no attempt will be to open a browser')

    options, args = parser.parse_args(argv)

    if len(args) != 1:
        parser.error('please provide the path to a profiler output file to '
                     'open')

    if options.browser and options.server:
        parser.error("options --browser and --server are mutually exclusive")

    filename = os.path.abspath(args[0])
    if not os.path.exists(filename):
        parser.error('the file %s does not exist' % filename)

    try:
        open(filename)
    except IOError as e:
        parser.error('the file %s could not be opened: %s'
                     % (filename, str(e)))

    filename = quote_plus(filename)

    hostname = options.hostname
    port = options.port

    if not 0 <= port <= 65535:
        parser.error('invalid port number %d: use a port between 0 and 65535'
                     % port)

    # Go ahead and import the tornado app and start it; we do an inline import
    # here to avoid the extra overhead when just running the cli for --help and
    # the like
    from .main import app
    import tornado.ioloop

    # As seen in IPython:
    # https://github.com/ipython/ipython/blob/8be7f9abd97eafb493817371d70101d28640919c/IPython/html/notebookapp.py
    # See the IPython license at:
    # https://github.com/ipython/ipython/blob/master/COPYING.rst.
    for p in random_ports(port, 10):
        try:
            app.listen(p, address=hostname)
        except socket.error as e:
            print('Port {0} in use, trying another.'.format(p))
        else:
            port = p
            break
    else:
        print('No available port found.')
        return 1

    url = "http://{0}:{1}/snakeviz/{2}".format(hostname, port, filename)
    print(('snakeviz web server started on %s:%d; enter Ctrl-C to exit' %
           (hostname, port)))
    print(url)

    if not options.server:
        try:
            browser = webbrowser.get(options.browser)
        except webbrowser.Error as e:
            parser.error('no web browser found: %s' % e)

        # Launch the browser in a separate thread to avoid blocking the
        # ioloop from starting
        def bt():
            browser.open(url, new=2)
        threading.Thread(target=bt).start()

    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        # TODO: Cheap KeyboardInterrupt handler for now; iPython has some nicer
        # stuff for handling SIGINT and SIGTERM that might be worth borrowing
        tornado.ioloop.IOLoop.instance().stop()
        print('\nBye!')

    return 0
