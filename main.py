#!/usr/bin/env python

import os.path

import tornado.ioloop
import tornado.web

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'debug': True
}

import handler

class SunburstHandler(handler.Handler):
    def get(self):
        self.render('sunburst.html')

handlers = [(r'/', 'upload.UploadHandler'),
            (r'/(.*)\.json', 'upload.JSONHandler'),
            (r'/sunburst', SunburstHandler)]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
