import yaml

from snakeviz.pstatsloader import PStatsNode
from snakeviz.testing import assert_call_graphs_match, temp_pstats_tree


def ptree_to_call_graph(tree):
    """Return dictionary representing the call graph of a PStats tree.

    Each node is either a single element dictionary or a string (leaf). Timing
    statistics are dropped from this graph---only function names are kept.
    """
    if tree.children:
        return {tree.name: [ptree_to_call_graph(c) for c in tree.children]}
    else:
        return tree.name


def ensure_call_graph(graph):
    """Ensure that we have a simple call graph dictionary.

    `PStatsNode` instances are converted to dictionary mapping node names to
    children.
    """
    if isinstance(graph, PStatsNode):
        graph = ptree_to_call_graph(graph)
    return graph


def test_call_graph():

    def sub_func():
        len([])

    def simple_func():
        len([])
        sub_func()

    expected_graph = yaml.load("""
        simple_func:
            - len
            - sub_func:
                - len
    """)

    with temp_pstats_tree('simple_func()', locals(), 'simple_func') as root:
        graph = ensure_call_graph(root)
        assert_call_graphs_match(graph, expected_graph)
