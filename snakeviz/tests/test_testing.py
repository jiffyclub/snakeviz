from collections import namedtuple

from snakeviz.testing import find_node


Node = namedtuple('Node', ('name', 'children'))


def test_find_node_in_linear_tree():
    # Tree: a -> b -> c
    c = Node(name='c', children=[])
    b = Node(name='b', children=[c])
    a = Node(name='a', children=[b])

    assert find_node(a, 'a') is a
    assert find_node(b, 'b') is b


def test_find_node_with_duplicate_name():
    # Tree: root  -> a -> b2
    #             -> b1
    b1 = Node(name='b', children=[])
    b2 = Node(name='b', children=[])
    a = Node(name='a', children=[b2])
    root = Node(name='root', children=[a, b1])

    assert find_node(root, 'b') is b1


def test_find_nonexistent_node():
    a = Node(name='a', children=[])

    assert find_node(a, 'b') is None
