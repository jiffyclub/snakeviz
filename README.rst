WebSnakeViz
===========

About
-----

WebSnakeViz is a viewer for Python profiling data that runs as a web
application in the browser. It is inspired by the wxPython profile viewer
`RunSnakeRun <http://www.vrplumber.com/programming/runsnakerun/>`_.

WSV is currently under active development but it is basically usable.
It is known to fail for some profiles and we're working to make it more robust.

Install
-------

You must current install WebSnakeViz from source. Either clone the repository
or download the zip file and then run `python setup.py install`.

Usage
-----

Use the `wsv` command to launch WebSnakeViz::

    wsv name_of_profile.prof

This will start a `Tornado <http://www.tornadoweb.org/>`_
web server and open the visualization in
your default browser. Use `control-C` to stop the server.
