"""
This module contains a Handler base class with a conveience method
for rendering templates with Jinja2. The Jinja2 environment
configuration is also here.

"""

import tornado.web
import jinja2
import os


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


class Handler(tornado.web.RequestHandler):
    """
    This is the base class for other handlers throughout snakeviz.
    It overrides tornado's `render` method with one that uses Jinja2.

    """
    def render_template(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **params):
        self.write(self.render_template(template, **params))
