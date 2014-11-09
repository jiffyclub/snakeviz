import yaml

from snakeviz.testing import assert_call_graphs_match, temp_pstats_tree
from snakeviz.upload import stats_to_tree_dict


def ptree_dict_to_call_graph(tree):
    """Return dictionary representing the call graph of a PStats tree.

    Each node is either a single element dictionary or a string (leaf). Timing
    statistics are dropped from this graph---only function names are kept.
    """
    children = tree.get('children')
    if children:
        return {tree['name']: [ptree_dict_to_call_graph(c) for c in children]}
    else:
        return tree['name']


def ptree_to_call_graph(tree, **kwargs):
    """Return a call graph from a PStatsLoader tree.

    This uses `stats_to_tree_dict` for testing.
    """
    tree_dict = stats_to_tree_dict(tree, **kwargs)
    return ptree_dict_to_call_graph(tree_dict)


def test_stats_to_tree_dict():

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
        graph = ptree_to_call_graph(root)
        assert_call_graphs_match(graph, expected_graph)

        graph = ptree_to_call_graph(root, max_depth=2)
        assert_call_graphs_match(graph, {'simple_func': ['len', 'sub_func']})
