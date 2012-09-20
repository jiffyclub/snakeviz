"""
This module contains the handlers for the upload page and the JSON
request URL. In the standalone, command line version the upload handler
is not used.

"""

import pstats
import json
import tempfile
import os
import multiprocessing as mp

from tornado import ioloop
from tornado.web import asynchronous

from . import pstatsloader
from . import handler


def storage_name(filename):
    """
    Prepend the temporary file directory to the input `filename`.

    Parameters
    ----------
    filename : str
        Any name to give a file.

    Returns
    -------
    tempname : str
        `filename` with temporary file directory prepended.

    """
    if len(filename) == 0:
        raise ValueError('filename must length greater than 0.')

    return os.path.join(tempfile.gettempdir(), filename)


class UploadHandler(handler.Handler):
    """
    Handler for a profile upload page. Not used in the command line
    version.

    """
    def get(self):
        self.render('upload.html')

    def post(self):
        filename = self.request.files['profile'][0]['filename']
        sfilename = storage_name(filename)

        # save the stats info to a file so it can be loaded by pstats
        with open(sfilename, 'wb') as f:
            f.write(self.request.files['profile'][0]['body'])

        # test whether this can be opened with pstats
        try:
            pstats.Stats(sfilename)

        except:
            os.remove(sfilename)
            error = 'There was an error parsing {0} with pstats.'
            error = error.format(filename)
            self.render('upload.html', error=error)

        else:
            self.redirect('viz/' + filename)


class JSONHandler(handler.Handler):
    """
    Handler for requesting the JSON representation of a profile.
    """

    _timer = None
    _pool = None
    _timeout = None
    _result = None

    @asynchronous
    def get(self, prof_name):
        if self.request.path.startswith('/json/file/'):
            if self.settings['single_user_mode']:
                if prof_name[0] != '/':
                    prof_name = '/' + prof_name
                filename = os.path.abspath(prof_name)
            else:
                self.send_error(status_code=404)
        else:
            filename = storage_name(prof_name)

        self._pool = mp.Pool(1, maxtasksperchild=1)
        self._result = self._pool.apply_async(prof_to_json, (filename,))

        # TODO: Make the timeout parameters configurable
        self._timeout = 10  # in seconds
        self._period = 0.1  # in seconds
        self._timer = ioloop.PeriodicCallback(self._result_callback,
                                              self._period * 1000,
                                              ioloop.IOLoop.instance())
        self._timer.start()

    def _result_callback(self):
        try:
            content = self._result.get(0)
            self._finish_request(content)
        except mp.TimeoutError:
            self._timeout -= self._period
            if self._timeout < 0:
                self._finish_request('')

    def _finish_request(self, content):
        self._timer.stop()
        self._pool.terminate()
        self._pool.close()
        if content:
            self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(content)
        self.finish()


def prof_to_json(prof_name):
    """
    Convert profiles stats in a `pstats` compatible file to a JSON string.

    Parameters
    ----------
    prof_name : str
        Path to to a `pstats` compatible profile.

    Returns
    -------
    json_stats : str
        Profile as a JSON string.

    """
    loader = pstatsloader.PStatsLoader(prof_name)

    d = _stats_to_tree_dict(loader.tree.children[0])

    return json.dumps(d, indent=1)


def _stats_to_tree_dict(node, parent=None, parent_size=None,
                        recursive_seen=None):
    """
    `_stats_to_tree_dict` is a specialized function for converting
    a `pstatsloader.PStatsLoader` profile representation into a tree
    of nested dictionaries by recursively calling itself.
    It is primarily meant to be called from `prof_to_json`.

    Parameters
    ----------
    node : `pstatsloader.PStatsRow` or `pstatsloader.PStatGroup`
        One node of the call tree.
    parent : `pstatsloader.PStatsRow` or `pstatsloader.PStatGroup`
        Parent of `node`. Optional for the root node.
    parent_size : float
        Calculated size of `parent`. Optional for the root node.
    recursive_seen : set
        Set of nodes that are direct ancestors of `node`.
        This is used to prevent `_stats_to_tree_dict` from ending up in
        infinite loops when it encounters recursion.
        Optional for the root node.

    Returns
    -------
    tree_dict : dict
        Tree of nested dictionaries representing the profile call tree.

    """
    # recursive_seen prevents us from repeatedly traversing
    # recursive structures. only want to show the first set.
    if recursive_seen is None:
        recursive_seen = set()

    d = {}

    d['name'] = node.name
    d['filename'] = node.filename
    d['directory'] = node.directory

    if isinstance(node, pstatsloader.PStatRow):
        d['calls'] = node.calls
        d['recursive'] = node.recursive
        d['local'] = node.local
        d['localPer'] = node.localPer
        d['cumulative'] = node.cummulative
        d['cumulativePer'] = node.cummulativePer
        d['line_number'] = node.lineno

        recursive_seen.add(node)

    if parent:
        # figure out the size of this node. This is an arbitrary value
        # but it's important that the child size is no larger
        # than the parent size.
        if isinstance(parent, pstatsloader.PStatGroup):
            if parent.cummulative:
                d['size'] = node.cummulative / parent.cummulative * parent_size
            else:
                # this is a catch-all when it's not possible
                # to calculate a size. hopefully this doesn't come
                # up too often.
                d['size'] = 0
        else:
            d['size'] = parent.child_cumulative_time(node) * parent_size
    else:
        # default size for the root node
        d['size'] = 1000

    if node.children:
        d['children'] = []
        for child in node.children:
            if child not in recursive_seen:
                child_dict = _stats_to_tree_dict(child, node, d['size'],
                                                 recursive_seen)
                d['children'].append(child_dict)

        if d['children']:
            # make a "child" that represents the internal time of this function
            children_sum = sum(c['size'] for c in d['children'])

            if children_sum > d['size']:
                for child in d['children']:
                    child['size'] = child['size'] / children_sum * d['size']

            elif children_sum < d['size']:

                d_internal = {'name': node.name,
                              'filename': node.filename,
                              'directory': node.directory,
                              'size': d['size'] - children_sum}

                if isinstance(node, pstatsloader.PStatRow):
                    d_internal['calls'] = node.calls
                    d_internal['recursive'] = node.recursive
                    d_internal['local'] = node.local
                    d_internal['localPer'] = node.localPer
                    d_internal['cumulative'] = node.cummulative
                    d_internal['cumulativePer'] = node.cummulativePer
                    d_internal['line_number'] = node.lineno

                d['children'].append(d_internal)
        else:
            # there were no non-recursive children so get rid of the
            # children list.
            del d['children']

    if node in recursive_seen:
        # remove this node from the set so it doesn't interfere if this
        # node shows up again in another part of the call tree.
        recursive_seen.remove(node)

    return d
