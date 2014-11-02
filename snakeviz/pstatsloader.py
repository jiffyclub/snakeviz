"""Module to load cProfile/profile records as a tree of records

The nodes (dict-values) of the PStats tree are timing tuples with:
    0. The number of times this function was called, not counting direct or
       indirect recursion.
    1. The number of times this function appears on the stack, minus one.
    2. Total time spent internal to this function.
    3. Cumulative time that this function was present on the stack.  In
       non-recursive functions, this is the total execution time from start to
       finish of each invocation of a function, including time spent in all
       sub-functions.
    4. A dictionary indicating the number of times each parent called us, with
       keys and values:

         {(module-path, line-number, function-name) : (tuple elements 0-to-3)}

Keys of the PStats tree are (module-path, line-number, function-name)-tuples,
just like the keys of node-value[4].

"""
from __future__ import print_function

import logging
import os
import pstats


log = logging.getLogger(__name__)

EPS = 1e-14


def cname(obj):
    return obj.__class__.__name__


def simple_repr(obj, attrs):
    kwargs = ', '.join(['{}={!r}'.format(k, getattr(obj, k)) for k in attrs])
    return '{}({})'.format(cname(obj), kwargs)


def raw_stats_to_nodes(stats):
    """ Convert a dictionary of timing stats to dictionary of PStatsNodes.

    Parameters
    ----------
    stats : dict
        Dictionary mapping functions (file, line, name) to profile timings.
        Typically, this will just be `pstats.Stats.stats`.
    """
    nodes = {}
    for func, raw_timing in stats.items():
        try:
            nodes[func] = PStatsNode(func, raw_timing)
        except ValueError:
            log.info('Null row: %s', func)

    for row in nodes.values():
        row.weave(nodes)
    return nodes


class PStatsLoader(object):
    """Load profiler statistic from files.

    This class uses function descriptors from `pstats` as keys for
    dictionaries, where a function is described by:

        (module-path, line-number, function-name)

    Attributes
    ----------
    nodes : dict
        Mapping from function descriptor to `PStatsNode`.
    tree : PStatsNode
        The root node of the profiler statistics tree. If there are multiple
        trees, only the slowest tree is stored here. See `forest` for more.
    forest : list
        The list of all profiler statistics trees.
    """

    def __init__(self, *filenames):
        self.filename = filenames
        self.stats = pstats.Stats(*filenames)
        self.nodes = raw_stats_to_nodes(self.stats.stats)
        self.tree = self._find_root(self.nodes)
        self.forest = self._find_forest(self.nodes, self.tree)

    @staticmethod
    def _find_root(nodes):
        """Attempt to find/create a reasonable root node from list/set of nodes

        TODO: still need more robustness here, particularly in the case of
        threaded programs.  Should be tracing back each row to root, breaking
        cycles by sorting on cumulative time, and then collecting the traced
        roots (or, if they are all on the same root, use that).

        """
        cumulative_times = sorted(nodes.values(), key=lambda x: x.t_cumulative)
        if not cumulative_times:
            raise RuntimeError("""Null results!""")
        return cumulative_times[-1]

    @staticmethod
    def _find_forest(nodes, root):
        forest = [root]

        for key, value in nodes.items():
            if not value.parents:
                log.debug('Found node root: %s', value)
                if value not in forest:
                    forest.append(value)
        return forest


class PStatsNode(object):
    """Simulates a HotShot profiler record using PStats module."""

    def __init__(self, caller, raw_timing):
        self.children = []
        self.parents = []

        fname, line, func = self.caller = caller
        try:
            dirname = os.path.dirname(fname)
            fname = os.path.basename(fname)
        except ValueError:
            dirname = ''

        nc, cc, tt, ct, callers = raw_timing

        if nc == cc == tt == ct == 0:
            raise ValueError('Null stats row')

        self.n_calls = nc
        self.n_calls_recursive = cc
        self.t_local = tt
        self.t_local_per_call = tt/max(cc, EPS)
        self.t_cumulative = ct
        self.t_cumulative_per_call = ct/max(nc, EPS)
        self.directory = dirname
        self.filename = fname
        self.name = func
        self.lineno = line
        self._callers = callers

    @property
    def n_children(self):
        return len(self.children)

    def __repr__(self):
        attrs = ['directory', 'filename', 'lineno', 'name', 'n_children']
        return simple_repr(self, attrs)

    def weave(self, nodes):
        for caller in self._callers.keys():
            parent = nodes.get(caller)
            if parent:
                self.parents.append(parent)
                parent.children.append(self)

    def child_cumulative_time(self, child):
        total = self.t_cumulative
        if total:
            try:
                (cc, nc, tt, ct) = child._callers[self.caller]
            except TypeError:
                ct = child._callers[self.caller]
            return float(ct)/total
        return 0
