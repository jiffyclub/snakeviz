import errno
import subprocess
import sys
import tempfile
import time
import uuid
from typing import Any, Literal, overload
from urllib.parse import quote

__all__ = ["load_ipython_extension"]


JUPYTER_HTML_TEMPLATE = """
<iframe id='snakeviz-{uuid}' frameborder=0 seamless width='100%' height='1000'></iframe>
<script>document.getElementById("snakeviz-{uuid}").setAttribute("src", "http://{host}:{port}{path}")</script>
"""
DEFAULT_HOST = "\" + document.location.hostname + \""

# Users may be using snakeviz in an environment where IPython is not
# installed, this try/except makes sure that snakeviz is operational
# in that case.
try:
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.core.magic import Magics, magics_class, line_cell_magic, line_magic
    from IPython.display import display, HTML
except ImportError:
    pass
else:

    @magics_class
    class SnakevizMagic(Magics):

        def __init__(self, shell: InteractiveShell | None = None,
                     **kwargs: Any) -> None:
            super().__init__(shell=shell, **kwargs)
            self._host = None
            self._port = None

        @line_cell_magic
        def snakeviz(self, line: str, cell: str | None = None) -> None:
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

            -t/--new-tab
            If running the snakeviz magic in the Jupyter Notebook,
            use this flag to open snakeviz visualization in a new tab
            instead of embedded within the notebook.

            Note that this will briefly open a server with host 0.0.0.0,
            which in some situations may present a slight security risk as
            0.0.0.0 means that the server will be available on all network
            interfaces (if they are not blocked by something like a firewall).

            """
            # get location for saved profile
            filename = tempfile.NamedTemporaryFile().name

            # parse options
            opts, line = self.parse_options(line, "t", "new-tab", posix=False)

            # call signature for prun
            line = "-q -D " + filename + " " + line

            # generate the stats file using IPython's prun magic
            ip = get_ipython()  # type: ignore[name-defined]

            if cell:
                ip.run_cell_magic("prun", line, cell)
            else:
                ip.run_line_magic("prun", line)

            sv: subprocess.Popen[Any]

            # start up a Snakeviz server
            if _check_ipynb() and not ("t" in opts or "new-tab" in opts):
                print("Embedding SnakeViz in this document...")
                sv = open_snakeviz_and_display_in_notebook(filename, self._host, self._port)
            else:
                print("Opening SnakeViz in a new tab...")
                sv = subprocess.Popen(
                    [sys.executable, "-m", "snakeviz", filename]
                )
            # give time for the Snakeviz page to load then shut down the server
            time.sleep(3)
            sv.terminate()

        @line_magic
        def snakeviz_config(self, line: str) -> None:
            """
            Configure the port and host name for snakeviz.

            This line magic takes two options, -h or -p (or alternatively the
            long forms --host and --post) for configuring the host and port,
            respectively, of the snakeviz server that is spun up when the
            snakeviz magic is called.

            The host is the url that will be used by the browser to connect
            to the server, and the port is the port used by the server and
            which will be supplied by the browser when it connects to the
            server.
            """
            opts, line = self.parse_options(line, "h:p:", "host=", "port=")
            for opt in opts:
                if opt in ("h", "host"):
                    self._host = opts[opt]
                elif opt in ("p", "port"):
                    self._port = opts[opt]
                else:
                    raise ValueError(f"Unsupported option {opt}.")
            host = self._host or DEFAULT_HOST
            port = self._port or "dynamically chosen"
            print(f"Snakeviz configured with host {host} and port {port}")


def load_ipython_extension(ipython: InteractiveShell) -> None:
    """Called when user runs %load_ext snakeviz"""
    ipython.register_magics(SnakevizMagic)


def _check_ipynb() -> bool:
    """
    Returns True if IPython is running as the backend for a
    Jupyter Notebook.

    """
    cfg = get_ipython().config  # type: ignore[name-defined]
    return "connection_file" in cfg["IPKernelApp"]


def open_snakeviz_and_display_in_notebook(
        filename: str,
        override_host: str | None = None,
        override_port: int | None = None) -> subprocess.Popen[str]:

    def _find_free_port() -> int:
        import socket
        from contextlib import closing

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            # snakeviz frequently gets called many times in a short period.
            # This line tells the kernel it's okay to reuse TIME-WAIT sockets,
            # which means snakeviz will use the same socket on successive runs,
            # which makes life with snakeviz-over-SSH much easier.
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            @overload
            def try_bind(port: Literal[0]) -> int: ...
            @overload
            def try_bind(port: int) -> int | None: ...
            def try_bind(port: int) -> int | None:
                try:
                    s.bind(("", port))
                except OSError as e:
                    if e.errno == errno.EADDRINUSE:
                        return None
                    else:
                        raise
                else:
                    return int(s.getsockname()[1])

            # Try a default range of five ports, then use whatever's free.
            for port in range(8080, 8085):
                if bound_port := try_bind(port):
                    return bound_port

            return try_bind(0)

    port = override_port or _find_free_port()

    def _start_and_wait_when_ready() -> subprocess.Popen[str]:
        import os

        environ = os.environ.copy()
        environ["PYTHONUNBUFFERED"] = "TRUE"
        sv = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "snakeviz",
                "-s",
                "-H",
                "0.0.0.0",
                "-p",
                str(port),
                filename,
            ],
            stdout=subprocess.PIPE,
            universal_newlines=True,
            env=environ,
        )
        while True:
            line = sv.stdout.readline() if sv.stdout else ''
            if line.strip().startswith("snakeviz web server started"):
                break
        return sv

    sv = _start_and_wait_when_ready()
    path = "/snakeviz/%s" % quote(filename, safe="")
    host = override_host or DEFAULT_HOST
    print(display)
    display(
        HTML(
            JUPYTER_HTML_TEMPLATE.format(
                port=port, path=path, uuid=uuid.uuid1(), host=host
            )
        )
    )
    return sv
