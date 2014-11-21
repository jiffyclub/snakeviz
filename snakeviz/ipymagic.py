import subprocess
import tempfile
import time

__all__ = ['load_ipython_extension']


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
    sv = subprocess.Popen(['snakeviz', filename])

    # give time for the Snakeviz page to load then shut down the server
    time.sleep(3)
    sv.terminate()


def load_ipython_extension(ipython):
    ipython.register_magic_function(snakeviz_magic, magic_kind='line_cell',
                                    magic_name='snakeviz')
