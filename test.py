from core import MRBT, verify
from random import sample

TEST_SIZE = 10000


def test_constructors_consistency():
    """
    __iter__
    from_iter
    from_dict
    __eq__
    """
    arr_ins = sample(list(range(TEST_SIZE)), TEST_SIZE)
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


def test_basic_functionality():
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
    arr_ins = sample(list(range(TEST_SIZE)), TEST_SIZE)
    arr_val = [str(k) for k in arr_ins]
    arr_mod = sample(arr_ins, len(arr_ins) // 10)
    arr_del = sample(arr_ins, len(arr_ins) // 10)

    t1 = MRBT()
    for i, item in enumerate(zip(arr_ins, arr_val)):
        if not i % 100:
            assert t1._test() is None
        t1.insert(*item)

    assert len(str(t1).split("\n")) == TEST_SIZE * 2 + 2

    for key in arr_ins:
        assert key in t1

    assert -1 not in arr_ins
    assert TEST_SIZE not in arr_ins

    t1.insert(0, "Changed, fail")

    for key in arr_ins[::100]:
        assert t1.get(key) == str(key)

    assert t1.get(-1) is None
    assert t1.get(TEST_SIZE) is None

    for i, key in enumerate(arr_mod):
        if not i % 10:
            assert t1._test() is None
        t1.set(key, "Changed")

    for key in arr_mod:
        assert t1.get(key) == "Changed"

    assert t1.size == len(t1)
    assert t1.size == TEST_SIZE

    for i, key in enumerate(arr_del):
        if not i % 10:
            assert t1._test() is None
        t1.delete(key)

    assert t1.size == len(t1)
    assert t1.size == TEST_SIZE - len(arr_del)


def test_validation():
    """
    digest
    get(verified=True)
    verify
    """
    arr_ins = sample(list(range(TEST_SIZE)), TEST_SIZE)
    arr_val = [str(k) for k in arr_ins]

    t1 = MRBT()
    for i, item in enumerate(zip(arr_ins, arr_val)):
        t1.insert(*item)
    t2 = MRBT()
    t2.insert(2, 3)

    val, vo = t1.get(TEST_SIZE // 2, verified=True)

    assert verify(t1.digest, vo)
    assert not verify(t2.digest, vo)


def test_extra_access():
    """
    by_keys_order
    __getitem__
    __setitem__
    """
    arr_ins = sample(list(range(TEST_SIZE)), TEST_SIZE)
    arr_val = [str(k) for k in arr_ins]

    t1 = MRBT()
    for i, item in enumerate(zip(arr_ins, arr_val)):
        if i % 2:
            t1[item[0]] = item[1]
        else:
            t1.insert(*item)

    for i in range(-TEST_SIZE, TEST_SIZE):
        res = t1.by_keys_order(i)
        assert res["key"] == (i + TEST_SIZE) % TEST_SIZE
        assert res["value"] == str(res["key"])

    assert t1.by_keys_order(-TEST_SIZE - 1) is None
    assert t1.by_keys_order(TEST_SIZE) is None

    for key in arr_ins[::100]:
        assert t1.get(key) == t1[key]


def test_get_change_set():
    """
    get_change_set
    """
    arr_ins = sample(list(range(TEST_SIZE)), TEST_SIZE)
    arr_val = [str(k) for k in arr_ins]
    arr_del = sample(arr_ins, len(arr_ins) // 100)

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
