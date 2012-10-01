#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup


import os


NAME = 'snakeviz'
VERSION = '0.1.1'


# Create a simple version.py module; less trouble than hard-coding the version
with open(os.path.join('snakeviz', 'version.py'), 'w') as f:
    f.write('__version__ = %r' % VERSION)

# Load up the description from README.rst
with open('README.rst') as f:
    DESCRIPTION = f.read()


setup(
    name=NAME,
    version=VERSION,
    author='Matt Davis',
    author_email='jiffyclub@gmail.com',
    url='https://github.com/jiffyclub/snakeviz',
    description='A web-based viewer for Python profiler output',
    long_description=DESCRIPTION,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: JavaScript',
        'Topic :: Software Development'
    ],
    packages=['snakeviz'],
    package_data={
        'snakeviz': ['static/*.ico',
                     'static/bootstrap/js/*.js',
                     'static/bootstrap/css/*.css',
                     'static/bootstrap/img/*.png',
                     'static/tooltip/*.js',
                     'static/tooltip/*.css',
                     'static/viz/*.js',
                     'static/*.js',
                     'templates/*.html']
    },
    install_requires=['tornado>=2.0', 'jinja2>=2.0'],
    entry_points={
        'console_scripts': ['snakeviz = snakeviz.cli:main']
    }
)
