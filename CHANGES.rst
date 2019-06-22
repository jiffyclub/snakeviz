v2.0.1
===================

* Fixes to SnakeViz embedding so that it doesn't assume jQuery is available
  when configuring the SnakeViz iframe.
* Add a set of default ports attempted when starting SnakeViz for
  embedding within Jupyter (Thanks @andyljones in #125!).

v2.0.0
===================

* ``%snakeviz`` IPython magic command now embeds the snakeviz visualization
  within a Jupyter Notebook when invoked from the notebook. This is the
  default behavior when it's used within a Notebook.
  (Thanks @yjmade via #110!)
* Improved error message when ``pstats.Stats`` can't load a profile.

v1.0.0
===================

* Change default visualization style to icicle
* Render directory contents (Thanks @pankajp in #95!)
* Allow modifying root node of visualization by clicking on table rows
  (Thanks @bmerry in #90!)
* Allow running snakeviz via ``python -m snakeviz.cli``
  (Thanks @pankajp in #94!)
* Allow running snakeviz via ``python -m snakeviz``
  (Thanks @orlp in #108!)
* Change default visualization depth to 10
  (Thanks @takluyver in #114!)

v0.4.2 (2017-08-13)
===================

* Improvements to section proportioning (Thanks @nschloe in #79!)
* Drop official Python 2.6 support

v0.4.1 (2016-05-02)
===================

* Labels added to icicle view (Thanks @thomasjm!)
* Bug fix functions with no identified callers (Thanks @embray!)

v0.4.0 (2015-04-03)
===================

* Add icicle plot option. (Thanks @yxiong!)

v0.3.1 (2015-03-23)
===================

* Allow users to move the visualization through the call stack
  by clicking on items in the call stack list. (Thanks @yxiong!)

v0.3.0 (2015-03-13)
===================

* Add a "server-only" mode so SnakeViz can be started without
  it trying to open a browser
* When starting the server, print a complete URL for viewing the profile
* Get rid of dict/set comprehensions so SnakeViz works on Python 2.6
* Fix a potential division-by-zero error

v0.2.1 (2014-11-30)
===================

* Try loading JS libraries from a CDN in the web worker so that it can
  be restarted even if the SnakeViz server has been shut down
  (as happens when using the IPython magic).

v0.2 (2014-11-30)
=================

* Near-complete rewrite of SnakeViz for improved performance and usability
* Most of the computation and call-tree building now happens in the client,
  once the page is loaded it is self-sufficient
* Display function info beside the sunburst instead of in tooltips
* Option to display the current call stack (useful when zooming)
* Controls for limiting depth of visualization and display of small functions

v0.1.4 (2014-10-15)
===================

* Fix display of functions in pstats table
* Sort pstats table on total time column be default

v0.1.3 (2014-10-14)
===================

* Switch to DataTables for table display
* Store all client assets in distribution for offline use

v0.1.2 (2014-10-13)
===================

* ``%snakeviz`` and ``%%snakeviz`` magics for IPython
* Python 3 support
* Fix for tooltips when the cursor is on the right side of the viz
* Remove use of the Bootstrap glyphicons
