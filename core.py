
"""
General TODO:
    1. MRBT class: implement compare, dumps, __len__, __iter__, k_largest methods.
    2. Increase readability.
    3. Compress code logic.
    4. Node class: allow custom `hash(l, r) -> hsh` functions in constructor.
    5. Update README.md.
"""


import hashlib
from math import inf as INF

__all__ = ["MRBT"]

RED = "RED"
BLACK = "BLACK"
NIL = "NIL"


class Node:
    def __init__(self, color=RED,
                 parent=None, left=None, right=None,
                 key: int = None, val=None) -> None:
        self.color = color
        self.parent = parent
        self.left = left
        self.right = right
        self.key = key

        self.val = None
        self.digest = [bytes(), bytes()]
        if self.color == NIL and self.key != INF:
            self.digest[1] = int(self.key).to_bytes(257, "little")
            self.store(val)

    def store(self, val):
        """
        Update stored value.
        """

        self.val = val

    def unite_digest(self):
        """
        Internal digests composition to lift upward.
        """

        hsh = hashlib.sha256(self.digest[0] + self.digest[1])
        return hsh.digest()

    def update_digest(self):
        """
        Updates digests for internal node or generate new for leaves.
        """

        if self.color == NIL:
            self.digest[0] = self.unite_digest()
        else:
            self.digest[0] = self.left.unite_digest()
            self.digest[1] = self.right.unite_digest()

    """
    Allows `Node()[x]` access for left and right childs.
    """

    def __getitem__(self, direction):
        if direction in ["L", 0, False]:
            return self.left
        else:
            return self.right

    def __setitem__(self, direction, node):
        if direction in ["L", 0, False]:
            self.left = node
        else:
            self.right = node

    """
    Boolean checks.
    """

    def is_root(self):
        return self.parent is None

    def is_child(self):
        return not self.is_root()

    def is_left_child(self):
        return self.is_child() and (self.key <= self.parent.key)

    def is_right_child(self):
        return self.is_child() and (self.key > self.parent.key)

    """
    Getting relatives.
    """

    def get_sibling(self):
        if self.is_root():
            return None
        if self.is_left_child():
            return self.parent.right
        else:
            return self.parent.left

    def get_grandparent(self):
        if self.is_root() or self.parent.is_root():
            return None
        return self.parent.parent

    def get_uncle(self):
        if self.is_root():
            return None
        return self.parent.get_sibling()

    """
    Miscellaneous.
    """

    def __str__(self, indent="  "):
        """
        Node recursive string representation.
        """

        b = "()" if self.color != NIL else "[]"
        res = indent[:-2] + " ⎣" + \
            "{} {}\n".format(b[0] + self.color[0] + b[1], self.key)
        if self.color != NIL:
            res += self.right.__str__(indent + " |")
            res += self.left.__str__(indent + "  ")
        return res


class MRBT:
    """
    Merkle Red-Black Tree.
    """

    def __init__(self, ) -> None:
        self.root = Node(NIL, key=INF)

    def _search(self, key, pair=False):
        """
        Performs binary `key` search.
        Returns:
            1. `False` AND list with termination leaf if `key` is not present.
            2. `True` AND list containing `key` internal node if `pair` if False.
            3. `True` AND list containing `key` internal node and leaf if `pair` is True.
        """

        focus = self.root
        found = True
        res = []
        while focus.color != NIL:
            if key == focus.key:
                res.append(focus)
                if not pair:
                    return True, res
            if key <= focus.key:
                focus = focus[0]
            elif key > focus.key:
                focus = focus[1]
        res.append(focus)
        found = (key == focus.key)
        return found, res

    def insert(self, key: int, val=None) -> None:
        """
        Performs `key` `val` insertion.
        Ignores if `key` is present.
        """

        found, search_result = self._search(key, pair=True)
        if found:
            return

        focus = search_result[-1]
        direction = focus.is_left_child()

        insertion_leaf = Node(NIL, key=key, val=val)
        insertion_node = Node(parent=focus.parent,
                              left=insertion_leaf,
                              right=focus, key=key)
        insertion_leaf.parent = insertion_node
        if focus.is_root():
            self.root = insertion_node
        else:
            focus.parent[1 - direction] = insertion_node
        focus.parent = insertion_node

        self._insert_fix(insertion_node)

    def delete(self, key: int) -> None:
        """
        Performs `key` deletion.
        Ignores if `key` is not present.
        """

        found, search_result = self._search(key, pair=True)
        if not found:
            return

        focus = search_result[-1]
        if focus.key != focus.parent.key:
            search_result[0].key = focus.parent.key

        parent = focus.parent
        sibling = focus.get_sibling()

        d_black = (parent.color != RED) and (sibling.color != RED)

        if parent.is_root():
            self.root = sibling
        else:
            direction_1 = parent.is_left_child()
            parent.parent[1 - direction_1] = sibling
        sibling.parent = parent.parent

        if sibling.color == RED:
            sibling.color = BLACK

        self._delete_fix(sibling, d_black)

    def get(self, key: int, auth=False):
        """
        Allows `MRBT().get(key, auth)` value access.
        Returns:
            1. `None` object if `key` is not present.
            2. Stored `key` value if `key` is present and `auth` is false.
            3. Stored `key` value AND verification object
               if `key` is present and `auth is true.
        """

        found, search_result = self._search(key, pair=True)
        if not found:
            return None

        focus = search_result[-1]

        if not auth:
            return focus.val

        vo = []
        while focus is not None:
            vo.append(focus.digest)
            focus = focus.parent
        return focus.val, tuple(vo)

    def set(self, key: int, val):
        """
        Allows `key` `val` modification.
        Ignores if `key` is not present.
        """

        found, search_result = self._search(key, pair=True)
        if not found:
            return
        focus = search_result[-1]
        focus.store(val)
        while focus is not None:
            focus.update_digest()
            focus = focus.parent

    def compare(self, other):
        pass

    def __contains__(self, key: int) -> bool:
        """
        Allows `key in MRBT()` syntax for key presence check.
        """

        return self._search(key)[0]

    def __getitem__(self, key: int):
        """
        Allows `MRBT()[key]` value access.
        Returns:
            1. `None` object if `key` is not present.
            2. Stored `key` value if `key` is present.
        """

        return self.get(key)

    def __setitem__(self, key: int, val) -> None:
        """
        Allows `MRBT()[key] = val` syntax.
        Updates key value or inserts it if not present.
        """

        found, search_result = self._search(key, pair=True)
        if not found:
            return self.insert(key, val)
        focus = search_result[-1]
        focus.store(val)
        while focus is not None:
            focus.update_digest()
            focus = focus.parent

    def __eq__(self, other) -> bool:
        """
        Allows simple equality checks by root digests comparison.
        False positives are highly unlikely to occur with proper Node() hashing definition.
        """

        return self.root.digest == other.root.digest

    def __str__(self):
        """
        String object representation.
        """

        return self.root.__str__()

    def _rotate(self, node):
        """
        Rotates node's parent over node's direction.
        """

        direction = node.is_left_child()
        parent = node.parent
        subtree = node[direction] if node.color != NIL else None

        if parent.is_root():
            self.root = node
        else:
            direction_1 = parent.is_left_child()
            parent.parent[1 - direction_1] = node
        node.parent = parent.parent

        node[direction] = parent
        parent.parent = node
        parent[1 - direction] = subtree
        if subtree is not None:
            subtree.parent = parent

    def _insert_fix(self, focus) -> None:
        """
        Insertion balancing with hash updates.
        """

        while focus.is_child() and focus.parent.color == RED:
            P = focus.parent
            G = focus.get_grandparent()
            U = focus.get_uncle()
            if G is None:
                break
            if U.color == RED:  # CASE 1
                P.color = BLACK
                U.color = BLACK
                G.color = RED
                focus.update_digest()
                P.update_digest()
                focus = G
                continue
            if focus.is_left_child() != focus.parent.is_left_child():  # CASE 2
                self._rotate(focus)
                focus = P
                continue
            else:  # CASE 3
                focus.update_digest()
                self._rotate(P)
                focus = G
                P.color = BLACK
                G.color = RED
                continue
        self.root.color = BLACK  # CASE 0

        while focus is not None:
            focus.update_digest()
            focus = focus.parent

    def _delete_fix(self, focus, d_black=False) -> None:
        """
        Deletion balancing with hash updates.
        """

        while d_black:
            direction = int(focus.is_left_child())
            P = focus.parent
            S = focus.get_sibling()
            if S is not None and S.color != NIL:
                Sc = [S[0], S[1]]

            if P is None:  # CASE 1
                d_black = False
                continue
            if S.color == RED:  # CASE 2
                self._rotate(S)
                S.color = BLACK
                P.color = RED
                continue
            if P.color == BLACK and S.color == BLACK:
                if Sc[0].color != RED and Sc[1].color != RED:  # CASE 3
                    S.color = RED
                    focus.update_digest()
                    focus = P
                    continue
            if P.color == RED:
                if Sc[0].color != RED and Sc[1].color != RED:  # CASE 4
                    P.color = BLACK
                    S.color = RED
                    d_black = False
                    continue
            if S.color == BLACK:
                if Sc[direction].color == RED:  # CASE 6
                    self._rotate(S)
                    S.color = P.color
                    P.color = BLACK
                    Sc[direction].color = BLACK
                    d_black = False
                    continue
                if Sc[1 - direction].color == RED:  # CASE 5
                    self._rotate(S[1 - direction])
                    Sc[1 - direction].color = BLACK
                    S.color = RED
                    S.update_digest()
                    Sc[1 - direction].update_digest()
                    continue

        while focus is not None:
            focus.update_digest()
            focus = focus.parent

    def _test(self):
        """
        Test structure for:
            1. Linkage consistency.
            2. Black root.
            3. Constant black depth.
            4. Absence of red-red relationships.
            5. Each node either leaf or has 2 children.
        Assuming BST and Merkle properties are present.
        """

        assert self.root.color != RED
        focus = self.root
        last_not_red = True
        from_left = True
        move = "D"
        bbalance = 0
        bbalance_leaf = -1
        while focus != None:
            assert focus.left is None or focus.left.parent is focus
            assert focus.right is None or focus.right.parent is focus
            assert focus.is_child() or self.root is focus
            assert focus.left is not None or focus.color == NIL
            assert focus.right is not None or focus.color == NIL
            if move == "D":
                if focus.color != RED:
                    bbalance += 1
                else:
                    assert last_not_red
                last_not_red = (focus.color != RED)
                if focus.color == NIL:
                    if bbalance_leaf == -1:
                        bbalance_leaf = bbalance
                    assert bbalance == bbalance_leaf
                    move = "U"
                    from_left = focus.is_left_child()
                    focus = focus.parent
                else:
                    focus = focus.left
                    move = "D"
            else:
                if last_not_red:
                    bbalance -= 1
                last_not_red = (focus.color != RED)
                if from_left:
                    focus = focus.right
                    move = "D"
                else:
                    move = "U"
                    from_left = focus.is_left_child()
                    focus = focus.parent


"""
def test():
    import numpy as np
    a = MRBT()
    # arr = [9, 15,  7, 16, 19,  0,  8,  2,  1,  3]
    # ard = [1,  2,  3, 19,  0,  8,  9, 16, 15,  7]
    arr = np.random.choice(np.arange(10000), 10000, replace=False)
    ard = np.random.choice(arr, 10000, replace=False)

    for i in arr:
        print(i, end=" ")
        a.insert(i)
        a._test()
        print("INSERTED")
    for i in ard:
        print(i, end=" ")
        a.delete(i)
        a._test()
        print("DELETED")


if __name__ == "__main__":
    test()
"""
