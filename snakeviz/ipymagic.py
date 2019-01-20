import subprocess
import tempfile
import time
import uuid
import urllib

__all__ = ['load_ipython_extension']


JUPYTER_HTML_TEMPLATE = """
<iframe id='snakeviz-{uuid}' frameborder=0 seamless width='100%' height='1000'></iframe>
<script>$("#snakeviz-{uuid}").attr({{src:"http://"+document.location.hostname+":{port}{path}"}})</script>
"""


# Users may be using snakeviz in an environment where IPython is not
# installed, this try/except makes sure that snakeviz is operational
# in that case.
try:
    from IPython.core.magic import Magics, magics_class, line_cell_magic
    from IPython.display import display, HTML
except ImportError:
    pass
else:
    @magics_class
    class SnakevizMagic(Magics):

        @line_cell_magic
        def snakeviz(self, line, cell=None):
            """
            Profile code and display the profile in Snakeviz.
            Works as a line or cell magic.

            Usage, in line mode:
            %snakeviz [options] statement

            Usage, in cell mode:
            %%snakeviz [options] [statement]
            code...
            code...

            Options:

            -e/--embed
            If running the snakeviz magic in the Jupyter Notebook,
            use this flag to embed the snakeviz visualization within
            the notebook instead of trying to open a new tab.

            """
            # get location for saved profile
            filename = tempfile.NamedTemporaryFile().name

            # parse options
            opts, line = self.parse_options(line, 'e', 'embed', posix=False)

            # call signature for prun
            line = '-q -D ' + filename + ' ' + line

            # generate the stats file using IPython's prun magic
            ip = get_ipython()

            if cell:
                ip.run_cell_magic('prun', line, cell)
            else:
                ip.run_line_magic('prun', line)

            # start up a Snakeviz server
            if _check_ipynb() and ('e' in opts or 'embed' in opts):
                sv = open_snakeviz_and_display_in_notebook(filename)
            else:
                sv = subprocess.Popen(['snakeviz', filename])
            # give time for the Snakeviz page to load then shut down the server
            time.sleep(3)
            sv.terminate()


def load_ipython_extension(ipython):
    """Called when user runs %load_ext snakeviz"""
    ipython.register_magics(SnakevizMagic)


def _check_ipynb():
    """
    Returns True if IPython is running as the backend for a
    Jupyter Notebook.

    """
    cfg = get_ipython().config
    return "connection_file" in cfg["IPKernelApp"]


def open_snakeviz_and_display_in_notebook(filename):

    def _find_free_port():
        import socket
        from contextlib import closing
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    port = str(_find_free_port())

    def _start_and_wait_when_ready():
        import os
        environ = os.environ.copy()
        environ["PYTHONUNBUFFERED"] = "TRUE"
        sv = subprocess.Popen(
            ['snakeviz', "-s", "-p", port, filename],
            stdout=subprocess.PIPE, universal_newlines=True, env=environ)
        while True:
            line = sv.stdout.readline()
            if line.strip().startswith("snakeviz web server started"):
                break
        return sv

    sv = _start_and_wait_when_ready()
    path = "/snakeviz/%s" % urllib.parse.quote_plus(filename)
    display(HTML(JUPYTER_HTML_TEMPLATE.format(
        port=port, path=path, uuid=uuid.uuid1())))
    return sv
