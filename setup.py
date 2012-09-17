#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup


import os


NAME = 'snakeviz'
VERSION = '0.1.dev'


# Create a simple version.py module; less trouble than hard-coding the version
with open(os.path.join('snakeviz', 'version.py'), 'w') as f:
    f.write('__version__ = %r' % VERSION)


setup(
    name=NAME,
    version=VERSION,
    author='Matt Davis',
    author_email='jiffyclub@gmail.com',
    url='https://github.com/jiffyclub/snakeviz',

    packages=['snakeviz'],
    package_data={
        'snakeviz': ['static/*.ico',
                     'static/bootstrap/js/*.js',
                     'static/bootstrap/css/*.css',
                     'static/tooltip/js/*.js',
                     'static/tooltip/css/*.css',
                     'static/viz/js/*.js',
                     'static/viz/css/*.css',
                     'templates/*.html']
    },
    install_requires=['tornado>=2.0', 'jinja2>=2.0'],
    entry_points={
        'console_scripts': ['snakeviz = snakeviz.cli:main']
    }
)
