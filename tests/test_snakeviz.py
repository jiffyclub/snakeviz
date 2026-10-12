import cProfile
import os
import glob
import shlex
import subprocess as sp
import tempfile
import time
from contextlib import contextmanager
from urllib.parse import quote

import pytest
import requests

from snakeviz import VERSION
from snakeviz import cli


@contextmanager
def snakeviz(fname, port=None):
    if port:
        args = f'snakeviz -s --port {port}'
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
    return 'http://localhost:{}/snakeviz/{}'.format(
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
    assert VERSION in out.decode('utf-8') or \
        VERSION in err.decode('utf-8')


@pytest.mark.parametrize('hostname, url_host', [
    ('127.0.0.1', '127.0.0.1'),
    ('localhost', 'localhost'),
    ('::1', '[::1]'),
    ('2001:db8::1', '[2001:db8::1]'),
])
def test_cli_url_hostname(tmp_path, monkeypatch, capsys, hostname, url_host):
    from snakeviz.main import app
    from tornado.ioloop import IOLoop

    addresses = []
    monkeypatch.setattr(app, 'listen',
                        lambda port, address: addresses.append(address))
    monkeypatch.setattr(IOLoop.instance(), 'start', lambda: None)

    assert cli.main(['-s', '-H', hostname, str(tmp_path)]) == 0
    assert addresses == [hostname]
    url = capsys.readouterr().out.splitlines()[-1]
    assert url == 'http://{}:8080/snakeviz/{}'.format(
        url_host, quote(str(tmp_path), safe=''))
