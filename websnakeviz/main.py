#!/usr/bin/env python

import os.path

import tornado.ioloop
import tornado.web

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'debug': True,
    'single_user_mode': False
}

handlers = [(r'/', 'websnakeviz.upload.UploadHandler'),
            (r'/json/file/(.*)\.json', 'websnakeviz.upload.JSONHandler'),
            (r'/json/(.*)\.json', 'websnakeviz.upload.JSONHandler'),
            (r'/viz/file/(.*)', 'websnakeviz.viz.VizHandler'),
            (r'/viz/(.*)', 'websnakeviz.viz.VizHandler')]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
