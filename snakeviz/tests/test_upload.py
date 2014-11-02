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
        tree_dict = stats_to_tree_dict(root)
        graph = ptree_dict_to_call_graph(tree_dict)
        assert_call_graphs_match(graph, expected_graph)
