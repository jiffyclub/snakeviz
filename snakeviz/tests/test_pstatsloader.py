import os
import profile
import tempfile
from contextlib import contextmanager

import yaml
from nose.tools import assert_equal

from snakeviz.pstatsloader import PStatsLoader, PStatRow


@contextmanager
def temp_file(suffix='', prefix='tmp', dir=None):
    fd, filename = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    try:
        yield filename
    finally:
        os.close(fd)
        os.unlink(filename)


@contextmanager
def temp_pstats_tree(command_str, locals_dict=None):
    """Yield temporary `PStatRow` with representing the root of the call graph.

    Parameters
    ----------
    command_str : str
        String with python command to execute and profile.
    locals_dict : dict
        Dictionary of local variables for command execution.
    """
    profiler = profile.Profile()
    profiler.runctx(command_str, globals(), locals_dict)

    with temp_file() as filename:
        profiler.dump_stats(filename)

        full_tree = PStatsLoader(filename).tree
        # The first child is always from the profiler,... I think.
        profiler_tree = full_tree.children[0]
        assert profiler_tree.name == 'setprofile'

        # The second child is what actually runs the command string.
        yield full_tree.children[1]


def ptree_to_call_graph(tree):
    """Return dictionary representing the call graph of a PStats tree.

    Each node is either a single element dictionary or a string (leaf).
    """
    if tree.children:
        return {tree.name: [ptree_to_call_graph(c) for c in tree.children]}
    else:
        return tree.name


def ensure_call_graph(graph):
    """Ensure that we have a simple call graph dictionary.

    `PStatRow` instances are converted to dictionary mapping node names to
    children.
    """
    if isinstance(graph, PStatRow):
        graph = ptree_to_call_graph(graph)
    return graph


def node_name(graph):
    assert len(graph) == 1
    return graph.keys()[0]


def get_children(graph):
    assert len(graph) == 1
    return graph.values()[0]


def is_leaf(node):
    return isinstance(node, basestring)


def has_children(node):
    return not is_leaf(node)


def get_barren_children(graph):
    """Return sorted list of children that have no offspring."""
    return sorted(c for c in get_children(graph) if is_leaf(c))


def get_fertile_children(graph):
    """Return sorted list of children that have offspring."""
    return sorted(c for c in get_children(graph) if has_children(c))


def assert_barren_children_match(*nodes):
    assert_equal(*[get_barren_children(n) for n in nodes])


def assert_graph_nodes_match(node, expected_node):
    if is_leaf(node):
        assert_equal(node, expected_node)
    else:
        assert_equal(node_name(node), node_name(expected_node))
        assert_barren_children_match(node, expected_node)

        children = get_fertile_children(node)
        expected_children = get_fertile_children(expected_node)
        assert_equal(len(children), len(expected_children))

        for subgraph, expected_subgraph in zip(children, expected_children):
            assert_graph_nodes_match(subgraph, expected_subgraph)


def assert_call_graphs_match(graph, expected_graph):
    """ Assert input graph matches the expected graph.

    Note that the ordering of children is ignored, since the PStats tree
    doesn't preserve call order.
    """
    graph = ensure_call_graph(graph)
    expected_graph = ensure_call_graph(expected_graph)

    assert_graph_nodes_match(graph, expected_graph)


def test_call_graph():

    def sub_func():
        len([])

    def simple_func():
        a = range(3)
        len(a)
        sub_func()


    expected_graph = yaml.load("""
        <module>:
            - simple_func:
                - range
                - len
                - sub_func:
                    - len
    """)

    with temp_pstats_tree('simple_func()', locals()) as root:
        assert_call_graphs_match(root, expected_graph)
