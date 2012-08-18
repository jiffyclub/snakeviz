#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup


import os


NAME = 'websnakeviz'
VERSION = '0.1.dev'


# Create a simple version.py module; less trouble than hard-coding the version
with open(os.path.join('websnakeviz', 'version.py'), 'w') as f:
    f.write('__version__ = %s' % VERSION)


setup(
    name=NAME,
    version=VERSION,
    author='Matt Davis',
    author_email='jiffyclub@gmail.com',
    url='https://github.com/jiffyclub/websnakeviz',

    packages=['websnakeviz'],
    package_data={
        'websnakeviz': ['static/*.ico', 'static/*.js', 'static/*.css',
                        'templates/*.css']
    },
    install_requires=['tornado>=2.0', 'jinja2>=2.0']
)
