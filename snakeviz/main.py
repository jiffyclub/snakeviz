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
        abspath = os.path.abspath(profile_name)
        if os.path.isdir(abspath):
            if not self.request.path.endswith('/'):
                return self.redirect(self.request.path + '/')
            return self._list_dir(abspath)
        try:
            s = Stats(profile_name)
        except:
            raise RuntimeError('Could not read %s.' % profile_name)
        self.render(
            'viz.html', profile_name=profile_name,
            table_rows=table_rows(s), callees=json_stats(s))

    def _list_dir(self, path):
        entries = os.listdir(path)
        dir_entries = []
        for name in entries:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
            dir_entries.append([[displayname, linkname]])
        self.render(
            'dir.html', profile_name=path, table_rows=dir_entries)

handlers = [(r'/snakeviz/(.*)', VizHandler)]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
