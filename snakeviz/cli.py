#!/usr/bin/env python
"""
This module contains the command line interface for snakeviz.

"""
from __future__ import print_function

import argparse
import os
import threading
import webbrowser


def main():
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument('filename', help="Python profile statistics.")
    parser.add_argument('-H', '--hostname',
                        metavar='ADDR', default='127.0.0.1',
                        help='hostname to bind to (default: 127.0.0.1')

    # TODO: Make this help text actually true
    parser.add_argument('-p', '--port', type=int,
                        metavar='PORT', default=8080,
                        help="port to bind to; if this port is already in use "
                             "a free port will be selected automatically "
                             "(default: %default)")

    parser.add_argument('-b', '--browser', metavar='PATH',
                        help="path to the web browser executable used to open "
                             "open the visualization; uses same default as "
                             "Python's webbrowser module, which can also be "
                             "overridden with BROWSER environment variable")

    parser.add_argument('-d', '--tree-depth', type=int, default=10,
                        help="Maximum depth of profile tree. Setting this "
                             "to a low number can fix upload issues with "
                             "large profile runs.")

    args = parser.parse_args()

    filename = os.path.abspath(args.filename)
    if not os.path.exists(filename):
        parser.error('the file %s does not exist' % filename)

    try:
        open(filename)
    except IOError as e:
        parser.error('the file %s could not be opened: %s'
                     % (filename, str(e)))

    hostname = args.hostname
    port = args.port

    if not 0 <= port <= 65535:
        parser.error('invalid port number %d: use a port between 0 and 65535'
                     % port)

    try:
        browser = webbrowser.get(args.browser)
    except webbrowser.Error as e:
        parser.error('no web browser found: %s' % e)

    # Go ahead and import the tornado app and start it; we do an inline import
    # here to avoid the extra overhead when just running the cli for --help and
    # the like
    from .main import create_app
    import tornado.ioloop

    json_kwargs = {'tree_depth': args.tree_depth}
    app = create_app(single_user_mode=True, json_kwargs=json_kwargs)
    app.listen(port, address=hostname)

    print(('snakeviz web server started on %s:%d; enter Ctrl-C to exit' %
           (hostname, port)))

    # Launce the browser in a separate thread to avoid blocking the ioloop from
    # starting

    import platform
    if platform.system() == 'Windows':
        filename = '/' + filename

    bt = lambda: browser.open('http://%s:%d/viz/file%s' %
                              (hostname, port, filename), new=2)
    threading.Thread(target=bt).start()

    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        # TODO: Cheap KeyboardInterrupt handler for now; iPython has some nicer
        # stuff for handling SIGINT and SIGTERM that might be worth borrowing
        tornado.ioloop.IOLoop.instance().stop()
        print('\nBye!')
