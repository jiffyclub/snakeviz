import subprocess
import tempfile
import time
from IPython.display import display, HTML
import uuid
import urllib

__all__ = ['load_ipython_extension']


JUPYTER_HTML_TEMPLATE = """
<iframe id='{uuid}' frameborder=0 seamless width='100%%' height='1000'></iframe>
<script>$("#{uuid}").attr({{src:"http://"+document.location.hostname+":{port}{path}"}})</script>
"""


def snakeviz_magic(line, cell=None):
    """
    Profile code and display the profile in Snakeviz.
    Works as a line or cell magic.

    """
    # get location for saved profile
    filename = tempfile.NamedTemporaryFile().name

    # call signature for prun
    line = '-q -D ' + filename + ' ' + line

    # generate the stats file using IPython's prun magic
    ip = get_ipython()

    if cell:
        ip.run_cell_magic('prun', line, cell)
    else:
        ip.run_line_magic('prun', line)

    # start up a Snakeviz server
    if _check_ipynb():
        port = str(_find_free_port())
        sv = subprocess.Popen(['snakeviz', "-s", "-H", "0.0.0.0", "-p", port, filename])
        time.sleep(0.5)
        path = "/snakeviz/%s" % urllib.parse.quote_plus(filename)
        # data = requests.get(url).content
        display(HTML(JUPYTER_HTML_TEMPLATE.format(port=port, path=path, uuid=uuid.uuid1())))
    else:
        sv = subprocess.Popen(['snakeviz', filename])
    # give time for the Snakeviz page to load then shut down the server
    time.sleep(3)
    sv.terminate()


def load_ipython_extension(ipython):
    ipython.register_magic_function(snakeviz_magic, magic_kind='line_cell',
                                    magic_name='snakeviz')


def _check_ipynb():
    cfg = get_ipython().config
    return "connection_file" in cfg["IPKernelApp"]


def _find_free_port():
    import socket
    from contextlib import closing
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]
