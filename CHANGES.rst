v0.3.1
======

* Allow users to move the visualization through the call stack
  by clicking on items in the call stack list.

v0.3.0
======

* Add a "server-only" mode so SnakeViz can be started without
  it trying to open a browser
* When starting the server, print a complete URL for viewing the profile
* Get rid of dict/set comprehensions so SnakeViz works on Python 2.6
* Fix a potential division-by-zero error

v0.2.1
======

* Try loading JS libraries from a CDN in the web worker so that it can
  be restarted even if the SnakeViz server has been shut down
  (as happens when using the IPython magic).

v0.2
====

* Near-complete rewrite of SnakeViz for improved performance and usability
* Most of the computation and call-tree building now happens in the client,
  once the page is loaded it is self-sufficient
* Display function info beside the sunburst instead of in tooltips
* Option to display the current call stack (useful when zooming)
* Controls for limiting depth of visualization and display of small functions

v0.1.4
======

* Fix display of functions in pstats table
* Sort pstats table on total time column be default

v0.1.3
======

* Switch to DataTables for table display
* Store all client assets in distribution for offline use

v0.1.2
======

* ``%snakeviz`` and ``%%snakeviz`` magics for IPython
* Python 3 support
* Fix for tooltips when the cursor is on the right side of the viz
* Remove use of the Bootstrap glyphicons
