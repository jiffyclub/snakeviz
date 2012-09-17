"""
This module contains the command line interface for snakeviz.

"""

import optparse
import os
import sys
import threading
import webbrowser


def main(argv=sys.argv[1:]):
    parser = optparse.OptionParser(
        usage='%prog [options] filename'
    )
    parser.add_option('-H', '--hostname', metavar='ADDR', default='127.0.0.1',
                      help='hostname to bind to (default: 127.0.0.1')

    # TODO: Make this help text actually true
    parser.add_option('-p', '--port', type='int', metavar='PORT', default=8080,
                      help='port to bind to; if this port is already in use a'
                           'free port will be selected automatically '
                           '(default: %default)')

    parser.add_option('-b', '--browser', metavar='PATH',
                      help="path to the web browser executable to use to open "
                           "the visualization; uses the same default as "
                           "Python's webbrowser module, which can also be "
                           "overridden with the BROWSER environment variable")

    options, args = parser.parse_args(argv)

    if len(args) != 1:
        parser.error('please provide the path to a profiler output file to '
                     'open')

    filename = os.path.abspath(args[0])
    if not os.path.exists(filename):
        parser.error('the file %s does not exist' % filename)

    try:
        open(filename)
    except IOError, e:
        parser.error('the file %s could not be opened: %s'
                     % (filename, str(e)))

    hostname = options.hostname
    port = options.port

    if not 0 <= port <= 65535:
        parser.error('invalid port number %d: use a port between 0 and 65535'
                     % port)

    try:
        browser = webbrowser.get(options.browser)
    except webbrowser.Error as e:
        parser.error('no web browser found: %s' % e)

    # Go ahead and import the tornado app and start it; we do an inline import
    # here to avoid the extra overhead when just running the cli for --help and
    # the like
    from .main import app
    import tornado.ioloop

    app.listen(8080, address=hostname)
    app.settings['single_user_mode'] = True

    print ('snakeviz web server started on %s:%d; enter Ctrl-C to exit' %
           (hostname, port))

    # Launce the browser in a separate thread to avoid blocking the ioloop from
    # starting
    # TODO: Fix filename handling on Windows at some point
    bt = lambda: browser.open('http://%s:%d/viz/file%s' %
                              (hostname, port, filename), new=2)
    threading.Thread(target=bt).start()

    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        # TODO: Cheap KeyboardInterrupt handler for now; iPython has some nicer
        # stuff for handling SIGINT and SIGTERM that might be worth borrowing
        tornado.ioloop.IOLoop.instance().stop()
        print ('\nBye!')

    return 0
