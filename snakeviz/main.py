#!/usr/bin/env python

import os.path
from pstats import Stats
import json

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

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
        abspath = os.path.abspath(profile_name)
        if os.path.isdir(abspath):
            self._list_dir(abspath)
        else:
            try:
                s = Stats(profile_name)
            except:
                raise RuntimeError('Could not read %s.' % profile_name)
            self.render(
                'viz.html', profile_name=profile_name,
                table_rows=table_rows(s), callees=json_stats(s))

    def _list_dir(self, path):
        """
        Show a directory listing.

        """
        entries = os.listdir(path)
        dir_entries = [[[
            '..',
            quote(os.path.normpath(os.path.join(path, '..')), safe='')
        ]]]
        for name in entries:
            if name.startswith('.'):
                # skip invisible files/directories
                continue
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname += '/'
            if os.path.islink(fullname):
                displayname += '@'
            dir_entries.append(
                [[displayname, quote(os.path.join(path, linkname), safe='')]])

        self.render(
            'dir.html', dir_name=path, dir_entries=json.dumps(dir_entries))


handlers = [(r'/snakeviz/(.*)', VizHandler)]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
