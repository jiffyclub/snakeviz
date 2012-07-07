#!/usr/bin/env python

import os.path
import pstats
import StringIO

import tornado.ioloop
import tornado.web

import handler

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'debug': True
}

class MainHandler(handler.Handler):
    def get(self):
        self.render('main.html')

    def post(self):
        with open(self.request.files['profile'][0]['filename'], 'wb') as f:
            f.write(self.request.files['profile'][0]['body'])

        s = StringIO.StringIO()

        stats = pstats.Stats(self.request.files['profile'][0]['filename'], stream=s)
        stats.print_stats()

        self.request.headers['Content-Type'] = 'text/plain'
        self.write(s.getvalue())

handlers = [(r'/', MainHandler)]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
