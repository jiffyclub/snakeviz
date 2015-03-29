import cProfile
import os
import glob
import shlex
import tempfile
import time
from contextlib import contextmanager
from subprocess import Popen

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

import pytest
import requests


@contextmanager
def snakeviz(fname, port=None):
    if port:
        args = 'snakeviz -s --port {0}'.format(port)
    else:
        args = 'snakeviz -s'

    args += ' ' + fname

    p = Popen(shlex.split(args))
    # give server time to start up
    time.sleep(1)
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


def test_snakeviz(prof, port):
    url = 'http://localhost:{0}/snakeviz/{1}'.format(
        port or 8080,  # default port for snakeviz
        quote_plus(prof))

    with snakeviz(prof, port=port):
        result = requests.get(url)

    result.raise_for_status()
    assert 'SnakeViz' in result.text
