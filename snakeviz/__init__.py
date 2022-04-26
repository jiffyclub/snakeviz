import os

with open(os.path.join('snakeviz', 'version.py'), 'w') as f:
    f.write('__version__ = version = %r' % "2.2")
from .version import __version__
from .ipymagic import *
