#!/usr/bin/env python

import os.path

import tornado.ioloop
import tornado.web


def create_app(single_user_mode=True, json_kwargs=None):
    """Create snakeviz Tornado app.

    Parameters
    ----------
    single_user_mode : bool
        If True, run in single-user mode, i.e. offline.
    """
    json_kwargs = {} if json_kwargs is None else json_kwargs

    if single_user_mode:
        handlers = [(r'/json/file/(.*)\.json',
                     'snakeviz.upload.JSONHandler', json_kwargs),
                    (r'/viz/file/(.*)', 'snakeviz.viz.VizHandler')]
    else:
        handlers = [(r'/', 'snakeviz.upload.UploadHandler'),
                    (r'/json/(.*)\.json',
                     'snakeviz.upload.JSONHandler', json_kwargs),
                    (r'/viz/(.*)', 'snakeviz.viz.VizHandler')]

    settings = {
        'static_path': os.path.join(os.path.dirname(__file__), 'static'),
        'debug': True,
        'single_user_mode': single_user_mode
    }
    return tornado.web.Application(handlers, **settings)


if __name__ == '__main__':
    app = create_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
