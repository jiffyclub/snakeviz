import cProfile
import os
import glob
import shlex
import subprocess as sp
import tempfile
import time
from contextlib import contextmanager

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

import pytest
import requests

from snakeviz import version


@contextmanager
def snakeviz(fname, port=None):
    if port:
        args = 'snakeviz -s --port {0}'.format(port)
    else:
        args = 'snakeviz -s'

    args += ' ' + fname

    p = sp.Popen(shlex.split(args))
    # give server time to start up
    time.sleep(3)
    yield
    p.terminate()


@pytest.fixture(scope='module')
def prof(request):
    with tempfile.NamedTemporaryFile() as f:
        fname = f.name
    cProfile.runctx('glob.glob("*")', {}, {'glob': glob}, fname)

    def fin():
        if os.path.exists(fname):
            os.remove(fname)
    request.addfinalizer(fin)

    return fname


@pytest.fixture(scope='module', params=[None, 9999])
def port(request):
    return request.param


def snakeviz_url(path, port):
    return 'http://localhost:{0}/snakeviz/{1}'.format(
        port or 8080,  # default port for snakeviz
        quote(path))


def test_snakeviz_profile(prof, port):
    url = snakeviz_url(prof, port)

    with snakeviz(prof, port=port):
        result = requests.get(url)

    result.raise_for_status()
    assert 'SnakeViz' in result.text


def test_snakeviz_dir(tmpdir, port):
    tmpdir.join('file.txt').write('contents')
    tmpdir.mkdir('subdir')
    url = snakeviz_url(str(tmpdir), port)

    with snakeviz(str(tmpdir), port=port):
        result = requests.get(url)
    result.raise_for_status()

    assert 'file.txt' in result.text
    assert 'subdir/' in result.text


def test_version():
    vcall = sp.Popen(
        ['snakeviz', '--version'], stdout=sp.PIPE, stderr=sp.PIPE)
    out, err = vcall.communicate()
    # in Python <= 3.3 this comes out on stderr, otherwise on stdout
    assert version.version in out.decode('utf-8') or \
        version.version in err.decode('utf-8')
