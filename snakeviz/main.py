#!/usr/bin/env python

import os.path
from pstats import Stats

try:
    from urllib.parse import unquote_plus
except ImportError:
    from urllib import unquote_plus

import tornado.ioloop
import tornado.web

from .stats import table_rows, json_stats

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'debug': True,
    'gzip': True
}


class VizHandler(tornado.web.RequestHandler):
    def get(self, profile_name):
        profile_name = unquote_plus(profile_name)
        s = Stats(profile_name)
        self.render(
            'viz.html', profile_name=profile_name,
            table_rows=table_rows(s), callees=json_stats(s))


handlers = [(r'/snakeviz/(.*)', VizHandler)]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
