#!/usr/bin/env python

import os.path

import tornado.ioloop
import tornado.web

import handler

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), "static"),
    'debug': True
}

class MainHandler(handler.Handler):
    def get(self):
        self.render('main.html')

handlers = [(r'/', MainHandler)]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
