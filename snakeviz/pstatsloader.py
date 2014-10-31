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

from gettext import gettext


log = logging.getLogger(__name__)

EPS = 1e-14


def cname(obj):
    return obj.__class__.__name__


class PStatsLoader(object):
    """Load profiler statistic from files."""

    def __init__(self, *filenames):
        self.filename = filenames
        self.stats = pstats.Stats(*filenames)
        self.nodes, self.tree = self._load_tree(self.stats.stats)
        self.location_nodes, self.location_tree = self._load_location_tree()

    def _load_tree(self, stats):
        """Build a squaremap-compatible model from a pstats class"""
        nodes = {}
        for func, raw_timing in stats.items():
            try:
                nodes[func] = PStatRow(func, raw_timing)
            except ValueError:
                log.info('Null row: %s', func)

        for row in nodes.values():
            row.weave(nodes)

        return nodes, self._find_root(nodes)

    def _find_root(self, nodes):
        """Attempt to find/create a reasonable root node from list/set of nodes

        Parameters
        ----------
        nodes: dict
            Mapping of ((module-path, line-number, function-name), PStatRow).

        TODO: still need more robustness here, particularly in the case of
        threaded programs.  Should be tracing back each row to root, breaking
        cycles by sorting on cumulative time, and then collecting the traced
        roots (or, if they are all on the same root, use that).

        """
        maxes = sorted(nodes.values(), key=lambda x: x.t_cumulative)
        if not maxes:
            raise RuntimeError("""Null results!""")

        root = maxes[-1]
        roots = [root]

        for key, value in nodes.items():
            if not value.parents:
                log.debug('Found node root: %s', value)
                if value not in roots:
                    roots.append(value)

        if len(roots) > 1:
            root = PStatGroup(
                directory='*',
                filename='*',
                name=gettext("<profiling run>"),
                children=roots,
            )
            root.finalize()
            nodes[root.caller] = root
        return root

    def _load_location_tree(self):
        """Build a squaremap-compatible model for location-based hierarchy."""
        directories = {}
        files = {}
        root = PStatGroup('/', 'PYTHONPATH')
        nodes = self.nodes.copy()

        for child in self.nodes.values():
            current = directories.get(child.directory)
            directory, filename = child.directory, child.filename

            if current is None:
                if directory == '':
                    current = root
                else:
                    current = PStatGroup(directory, '')
                    nodes[current.caller] = current
                directories[directory] = current

            if filename == '~':
                filename = '<built-in>'

            file_current = files.get((directory, filename))

            if file_current is None:
                file_current = PStatGroup(directory, filename)
                nodes[file_current.caller] = file_current
                files[(directory, filename)] = file_current
                current.children.append(file_current)

            file_current.children.append(child)

        # now link the directories...
        for key, value in directories.items():
            if value is root:
                continue
            found = False

            while key:
                new_key, rest = os.path.split(key)

                if new_key == key:
                    break

                key = new_key
                parent = directories.get(key)

                if parent:
                    if value is not parent:
                        parent.children.append(value)
                        found = True
                        break

            if not found:
                root.children.append(value)

        # lastly, finalize all of the directory records...
        root.finalize()
        return nodes, root


class BaseStat(object):

    def recursive_distinct(self, already_done=None, attribute='children'):
        if already_done is None:
            already_done = {}

        for child in getattr(self, attribute, ()):
            if child not in already_done:
                already_done[child] = True
                yield child
                gchildren = child.recursive_distinct(already_done=already_done,
                                                     attribute=attribute)
                for descendent in gchildren:
                    yield descendent

    def descendants(self):
        return list(self.recursive_distinct(attribute='children'))

    def ancestors(self):
        return list(self.recursive_distinct(attribute='parents'))


class PStatRow(BaseStat):
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
        self.callers = callers

    def __repr__(self):
        template = '{}({!r}, {!r}, {!r}, {!r}, {})'
        return template.format(cname(self), self.directory, self.filename,
                               self.lineno, self.name, len(self.children))

    def add_child(self, child):
        self.children.append(child)

    def weave(self, nodes):
        for caller, data in self.callers.items():
            # data is (cc, nc, tt, ct)
            parent = nodes.get(caller)
            if parent:
                self.parents.append(parent)
                parent.children.append(self)

    def child_cumulative_time(self, child):
        total = self.t_cumulative
        if total:
            try:
                (cc, nc, tt, ct) = child.callers[self.caller]
            except TypeError:
                ct = child.callers[self.caller]
            return float(ct)/total
        return 0


class PStatGroup(BaseStat):
    """A node/record that holds a group of children but isn't a raw-record
    based group

    Children with the name <module> are our "empty" space,
    our totals are otherwise just the sum of our children.

    Parameters
    ----------
    directory : str
        Directory (package) containing the executed module.
    filename : str
        File (module) containing the executed function.
    name : str
        Name of the executed function.

    """
    # If LOCAL_ONLY then only take the raw-record's local values, not
    # cumulative values
    LOCAL_ONLY = False

    def __init__(self, directory='', filename='', name='package',
                 children=None, local_children=None):
        self.directory = directory
        self.filename = filename
        self.name = ''
        self.caller = (directory, filename, name)
        self.children = children or []
        self.parents = []
        self.local_children = local_children or []

    def __repr__(self):
        template = '{}({!r}, {!r}, {!r})'
        return template.format(cname(self), self.directory,
                               self.filename, self.name)

    def finalize(self, already_done=None):
        """Finalize our values (recursively) taken from our children"""
        if already_done is None:
            already_done = {}
        if self in already_done:
            return True

        already_done[self] = True
        self.filter_children()
        children = self.children

        for child in children:
            if hasattr(child, 'finalize'):
                child.finalize(already_done)
            child.parents.append(self)

        self.calculate_totals(self.children, self.local_children)

    def filter_children(self):
        """Filter our children into regular and local children sets"""
        real_children = []
        for child in self.children:
            if child.name == '<module>':
                self.local_children.append(child)
            else:
                real_children.append(child)
        self.children = real_children

    def calculate_totals(self, children, local_children=None):
        """Calculate cumulative totals from children and/or local children"""
        pairs = (('n_calls_recursive', 'n_calls'), ('t_cumulative', 't_local'))

        for field, local_field in pairs:
            values = []

            for child in children:
                if isinstance(child, PStatGroup) or not self.LOCAL_ONLY:
                    values.append(getattr(child, field, 0))
                elif isinstance(child, PStatRow) and self.LOCAL_ONLY:
                    values.append(getattr(child, local_field, 0))

            value = sum(values)
            setattr(self, field, value)

        if self.n_calls_recursive:
            time = self.t_cumulative / float(self.n_calls_recursive)
            self.t_cumulative_per_call = time
        else:
            self.n_calls_recursive = 0

        if local_children:
            for field in ('t_local', 'n_calls'):
                value = sum([getattr(child, field, 0) for child in children])
                setattr(self, field, value)

            if self.n_calls:
                self.t_local_per_call = self.t_local / self.n_calls
        else:
            self.t_local = 0
            self.n_calls = 0
            self.t_local_per_call = 0


if __name__ == "__main__":
    import sys

    p = PStatsLoader(sys.argv[1])
    assert p.tree
    print(p.tree)
