#!/usr/bin/env python

import os.path

import tornado.ioloop
import tornado.web

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'debug': True,
    'single_user_mode': True
}

# set of handlers for online mode
# handlers = [(r'/', 'snakeviz.upload.UploadHandler'),
#             (r'/json/(.*)\.json', 'snakeviz.upload.JSONHandler'),
#             (r'/viz/(.*)', 'snakeviz.viz.VizHandler')]

# set of handlers for offline, single user mode
handlers = [(r'/json/file/(.*)\.json', 'snakeviz.upload.JSONHandler'),
            (r'/viz/file/(.*)', 'snakeviz.viz.VizHandler')]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
