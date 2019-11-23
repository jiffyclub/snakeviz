#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup


import os


NAME = 'snakeviz_study'
VERSION = '2.1.dev'


# Create a simple version.py module; less trouble than hard-coding the version
with open(os.path.join('snakeviz', 'version.py'), 'w') as f:
    f.write('__version__ = version = %r' % VERSION)

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
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development'
    ],
    packages=['snakeviz'],
    package_data={
        'snakeviz': ['static/*.ico',
                     'static/*.js',
                     'static/*.css',
                     'static/vendor/*.js',
                     'static/vendor/*.css',
                     'static/images/*.png',
                     'templates/*.html']
    },
    install_requires=['tornado>=2.0'],
    entry_points={
        'console_scripts': ['snakeviz = snakeviz.cli:main']
    }
)
