import os
import profile
import tempfile
from contextlib import contextmanager
try:
    import Queue as queue
except ImportError:
    import queue

from nose.tools import assert_equal

from snakeviz.pstatsloader import PStatsLoader


@contextmanager
def temp_file(suffix='', prefix='tmp', dir=None):
    fd, filename = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    try:
        yield filename
    finally:
        os.close(fd)
        os.remove(filename)


def find_node(root, name, _nodes=None):
    """Return node with given name based on breadth-first search."""
    _nodes = _nodes if _nodes is not None else queue.Queue()

    if root.name == name:
        return root
    else:
        for child in root.children:
            _nodes.put(child)
        if _nodes.qsize() == 0:
            return None

        return find_node(_nodes.get(), name, _nodes=_nodes)


@contextmanager
def temp_pstats_tree(command_str, locals_dict=None, root_name=None,
                     filter_names='default'):
    """Yield temporary `PStatsNode` representing the root of the call graph.

    Parameters
    ----------
    command_str : str
        String with python command to execute and profile.
    locals_dict : dict
        Dictionary of local variables for command execution.
    """
    if filter_names == 'default':
        filter_names = ['setprofile']

    profiler = profile.Profile()
    profiler.runctx(command_str, globals(), locals_dict)

    with temp_file() as filename:
        profiler.dump_stats(filename)

        tree = PStatsLoader(filename, filter_names=filter_names).tree
        if root_name is None:
            yield tree
        else:
            yield find_node(tree, root_name)


def node_name(graph):
    assert len(graph) == 1
    return list(graph.keys())[0]


def get_children(graph):
    assert len(graph) == 1
    return list(graph.values())[0]


def is_leaf(node):
    return not has_children(node)


def has_children(node):
    return hasattr(node, 'keys')


def get_barren_children(graph):
    """Return sorted list of children that have no offspring."""
    # XXX: Add node-name check to debug Travis issue.
    return sorted(c for c in get_children(graph)
                  if is_leaf(c))


def get_fertile_children(graph):
    """Return sorted list of children that have offspring."""
    return sorted(c for c in get_children(graph) if has_children(c))


def assert_barren_children_match(*nodes):
    assert_equal(*[get_barren_children(n) for n in nodes])


def assert_call_graphs_match(node, expected_node):
    """ Assert nodes of input graph matches the expected graph.

    Note that the ordering of children is ignored, since the PStats tree
    doesn't preserve call order.
    """
    if is_leaf(node):
        assert_equal(node, expected_node)
    else:
        assert_equal(node_name(node), node_name(expected_node))
        assert_barren_children_match(node, expected_node)

        children = get_fertile_children(node)
        expected_children = get_fertile_children(expected_node)
        assert_equal(len(children), len(expected_children))

        for subgraph, expected_subgraph in zip(children, expected_children):
            assert_call_graphs_match(subgraph, expected_subgraph)
