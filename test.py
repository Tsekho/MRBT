import pytest

from core import MRBT, verify
from math import ceil, inf as INF
from random import sample


def enum(*sequential, **named):
    """
    Easier enumeration
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type("Enum", (), enums)


COL = enum("RED", "BLACK", "NIL")


def consistency_check(tree: MRBT):
    """
    Test structure for:
        1. BST properties:
            - Correct keys ordering.
            - Linkage consistency.
            - Each node is either leaf or has 2 children.
        2. RBT properties:
            - Black root.
            - Constant black depth.
            - Absence of red-red relationships.
        3. Merkle properties:
            - Digests consistency.
        4. Miscellaneous:
            - Correct subtree size statistics.
            - Shortcut consistency.
            - Doubly linked list consistency.
    !!! Per-operation checks are quite slow for larger trees.
    ... Consider limiting either calls frequency or structure size.
    O(n).

    Returns
    -------
    str
        Message if a problem has been encountered.
    None
        If structure test passed.
    """
    # BST non-recursive DFS iteration.
    # Checks pretty much everything about links, weights and digests.
    if tree._root.color == COL.RED:
        return "Root is red."
    focus = tree._root
    left_border = []
    right_border = []
    last_not_red = True
    from_left = True
    move = "D"
    bbalance = 0
    bbalance_leaf = -1
    prev_leaf = None
    while focus != None:
        if move == "D":
            if focus.key == INF:
                if focus.shortcut is not None:
                    return "INF has shortcut."
                if focus.weight != 0:
                    return "INF has wrong weight."
                if focus.next is not None:
                    return "Wrong next."
                if focus.prev is not prev_leaf:
                    return "Wrong previous."
                if focus.prev is not None:
                    if focus.prev.next is not focus:
                        return "Wrong next."
            elif focus.color == COL.NIL:
                if focus[0] is not None or focus[1] is not None:
                    return "Leaf has children."
                if focus.weight != 1:
                    return "Leaf has wrong weight."
                if focus.prev is not prev_leaf:
                    return "Wrong previous."
                if focus.prev is not None:
                    if focus.prev.next is not focus:
                        return "Wrong next."
                prev_leaf = focus
            else:
                if focus[0] is None or focus[1] is None:
                    return "Node misses child."
                if focus.weight != focus[0].weight + focus[1].weight:
                    return "Node has wrong leaf."
                if not focus[0].is_child() or not focus[1].is_child():
                    return "Child has no parent."
                if focus[0].parent is not focus or focus[1].parent is not focus:
                    return "Child doesn't recognize parent."
            if focus.key != INF:
                if focus.shortcut is None:
                    return "Missing shortcut."
                if focus.shortcut.shortcut is None:
                    return "Missing back shortcut."
                if focus.shortcut.shortcut is not focus:
                    return "Invalid back shortcut."

            if len(left_border) and focus.key <= left_border[-1]:
                return "Child violated keys order."
            if len(right_border) and focus.key > right_border[-1]:
                return "Child violated keys order."
            if focus.digest != tree._calc_digest(focus):
                return "Digests are wrong."
            if focus.color != COL.RED:
                bbalance += 1
            else:
                if not last_not_red:
                    return "Red-red relationship."
            last_not_red = (focus.color != COL.RED)
            if focus.color == COL.NIL:
                if bbalance_leaf == -1:
                    bbalance_leaf = bbalance
                if bbalance != bbalance_leaf:
                    return "Black depth is inconsistent."
                from_left = focus.is_left_child()
                focus = focus.parent
                move = "U"
                if from_left and len(right_border):
                    right_border.pop()
                elif len(left_border):
                    left_border.pop()
            else:
                right_border.append(focus.key)
                focus = focus[0]
                move = "D"
        else:
            if last_not_red:
                bbalance -= 1
            last_not_red = (focus.color != COL.RED)
            if from_left:
                left_border.append(focus.key)
                focus = focus[1]
                move = "D"
            else:
                from_left = focus.is_left_child()
                focus = focus.parent
                move = "U"
                if from_left and len(right_border):
                    right_border.pop()
                elif len(left_border):
                    left_border.pop()
    return None


@pytest.mark.parametrize("test_size", [100, 1000, 10000])
def test_constructors_consistency(test_size):
    """
    __iter__
    from_iter
    from_dict
    __eq__
    """
    arr_ins = sample(list(range(test_size)), test_size)
    arr_val = [str(k) for k in arr_ins]
    dct_ins = {k: v for k, v in zip(arr_ins, arr_val)}

    t1 = MRBT()
    for item in zip(arr_ins, arr_val):
        t1.insert(*item)
    t2 = MRBT.from_iter(zip(arr_ins, arr_val))
    t3 = MRBT.from_dict(dct_ins)
    t4 = MRBT()

    assert t1 == t2
    assert t1 == t3
    assert t1 != t4


@pytest.mark.parametrize("test_size", [100, 1000, 10000])
def test_basic_functionality(test_size):
    """
    delete
    get(verified=False)
    insert
    set
    size
    __contains__
    __iter__
    __len__
    __str__
    """
    arr_ins = sample(list(range(test_size)), test_size)
    arr_val = [str(k) for k in arr_ins]
    arr_mod = sample(arr_ins, len(arr_ins) // 10)
    arr_del = sample(arr_ins, len(arr_ins) // 10)

    t1 = MRBT()
    for i, item in enumerate(zip(arr_ins, arr_val)):
        if not i % 100:
            assert consistency_check(t1) is None
        t1.insert(*item)

    assert len(str(t1).split("\n")) == test_size * 2 + 2

    for key in arr_ins:
        assert key in t1

    assert -1 not in arr_ins
    assert test_size not in arr_ins

    t1.insert(0, "Changed, fail")

    for key in arr_ins[::10]:
        assert t1.get(key) == str(key)

    assert t1.get(-1) is None
    assert t1.get(test_size) is None

    for i, key in enumerate(arr_mod):
        if not i % 10:
            assert consistency_check(t1) is None
        t1.set(key, "Changed")

    for key in arr_mod:
        assert t1.get(key) == "Changed"

    assert t1.size == len(t1)
    assert t1.size == test_size

    for i, key in enumerate(arr_del):
        if not i % 10:
            assert consistency_check(t1) is None
        t1.delete(key)

    assert t1.size == len(t1)
    assert t1.size == test_size - len(arr_del)


@pytest.mark.parametrize("test_size", [100, 1000, 10000])
def test_validation(test_size):
    """
    digest
    get(verified=True)
    verify
    """
    arr_ins = sample(list(range(test_size)), test_size)
    arr_val = [str(k) for k in arr_ins]

    t1 = MRBT()
    for i, item in enumerate(zip(arr_ins, arr_val)):
        t1.insert(*item)
    t2 = MRBT()
    t2.insert(2, 3)

    val, vo = t1.get(test_size // 2, verified=True)

    assert verify(t1.digest, vo)
    assert not verify(t2.digest, vo)


@pytest.mark.parametrize("test_size", [100, 1000, 10000])
def test_extra_access(test_size):
    """
    by_keys_order
    __getitem__
    __setitem__
    """
    arr_ins = sample(list(range(test_size)), test_size)
    arr_val = [str(k) for k in arr_ins]

    t1 = MRBT()
    for i, item in enumerate(zip(arr_ins, arr_val)):
        if i % 2:
            t1[item[0]] = item[1]
        else:
            t1.insert(*item)

    for i in range(-test_size, test_size):
        res = t1.by_keys_order(i)
        assert res["key"] == (i + test_size) % test_size
        assert res["value"] == str(res["key"])

    assert t1.by_keys_order(-test_size - 1) is None
    assert t1.by_keys_order(test_size) is None

    for key in arr_ins[::10]:
        assert t1.get(key) == t1[key]


@pytest.mark.parametrize("del_frac", [0.0001, 0.001, 0.01, 0.1])
@pytest.mark.parametrize("test_size", [100, 1000, 10000])
def test_get_change_set(test_size, del_frac):
    """
    get_change_set
    """
    arr_ins = sample(list(range(test_size)), test_size)
    arr_val = [str(k) for k in arr_ins]
    arr_del = sample(arr_ins, ceil(del_frac * test_size))

    t1 = MRBT()
    for i, item in enumerate(zip(arr_ins, arr_val)):
        t1.insert(*item)

    t2 = MRBT()
    for i, item in enumerate(zip(arr_ins, arr_val)):
        t2.insert(*item)

    for key in arr_del:
        t2.delete(key)

    assert len(t1.get_change_set(t2)) == len(arr_del)
    assert len(t2.get_change_set(t1)) == len(arr_del)

    for key in arr_del:
        t1.delete(key)

    assert len(t1.get_change_set(t2)) == 0
