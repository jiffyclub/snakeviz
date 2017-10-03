#!/usr/bin/env python

import os.path
from pstats import Stats

try:
    from urllib.parse import quote_plus, unquote_plus
except ImportError:
    from urllib import quote_plus, unquote_plus

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
    def get(self, profiles):
        profiles = unquote_plus(profiles)
        individual_profiles = profiles.split('&')

        # abspath = os.path.abspath(profile_name)  Already absolute from client
        if len(individual_profiles) == 1 and os.path.isdir(individual_profiles[0]):
            self._list_dir(individual_profiles[0])
        else:
            display_name = 'Multiple profiles' if len(individual_profiles)>1 else individual_profiles[0]
            try:
                s = Stats(*individual_profiles)  # Merge one or more profiles
            except Exception,e:
                raise RuntimeError('Error getting stats for %s: %s' % individual_profiles, str(e))
            self.render(
                'viz.html', display_name=display_name,
                table_rows=table_rows(s), callees=json_stats(s))

    def _list_dir(self, path):
        """
        Show a directory listing.

        """
        entries = os.listdir(path)
        dir_entries = [
            [['..', quote_plus(os.path.normpath(os.path.join(path, '..')))]]]
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
                [[displayname, quote_plus(os.path.join(path, linkname))]])

        self.render(
            'dir.html', dir_name=path, dir_entries=dir_entries)

handlers = [(r'/snakeviz/(.*)', VizHandler)]

app = tornado.web.Application(handlers, **settings)

if __name__ == '__main__':
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
