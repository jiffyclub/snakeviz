#!/usr/bin/env python

import pathlib
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
        self._check_if_allowed(abspath)
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

    def _check_if_allowed(self, abspath):
        """
        Checks if given file or directory is in allowed paths.
        """
        if not self.application._allowed_paths:
            # No filter set, allow all.
            return
        for path in self.application._allowed_paths:
            try:
                # If this doesn't raise, abspath is under path.
                pathlib.Path(abspath).relative_to(path)
                return
            except ValueError:
                continue
        raise RuntimeError('Path not allowed')

class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._allowed_paths = []

    def set_allowed_paths(self, paths):
        """
        Sets what paths are allowed to be retrieved.

        Call this with a list of strings, paths to files or directories that
        the server is allowed to display. Any directory arguments are treated
        as allowed prefixes, e.g., passing in ["/home/user/stuff"] will let you
        list "stuff" and retrieve any files under it.

        If not called, or called with an empty list, any restrictions are removed.
        """
        self._allowed_paths = []
        for path in paths:
            self._allowed_paths.append(pathlib.Path(path).resolve())


handlers = [(r'/snakeviz/(.*)', VizHandler)]

app = Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
