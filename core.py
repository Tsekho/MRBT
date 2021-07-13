"""
MRBT (Merkle Red-Black Tree)
---------
An efficient authenticated data structure
based on generic Red-Black Tree with Merkle augmentation.

Original Python 2 implementation:
    Andrew Miller.
    https://github.com/amiller/redblackmerkle
"""


__all__ = ["MRBT", "verify"]

import json
import hashlib
from math import inf as INF

RED = "RED"
BLACK = "BLACK"
NIL = "NIL"


def sha256_dual(a: bytes, b: bytes) -> bytes:
    return hashlib.sha256(a + b).digest()


class Node:
    """
    MRBT node.

    Parameters
    ----------
    key : int or float
        Stored key for search.
    color : str, default "RED"
        Either of "RED", "BLACK" or "NIL", represents node's color.
    parent : Node or None, default None
        Parent Node.
    left : Node or None, default None
        Left child Node.
    right : Node or None, default None
        Right child Node.
    val : object
        Stored data, must be json-serializable.
    """

    def __init__(self, key, color=RED,
                 parent=None, left=None, right=None,
                 val=None) -> None:
        self.color = color
        self.parent = parent
        self.left = left
        self.right = right
        self.key = key

        self.val = None
        self.digest = (bytes(), bytes())
        self.weight = 0
        if self.color == NIL and self.key != INF:
            self.store(val)
            self.weight = 1

    def store(self, val) -> None:
        """
        Update stored value.

        Parameters
        ----------
        val
            New value to store.
        """
        self.val = val

    def dump_key(self) -> bytes:
        """
        Return bytes representation of node's key.
        """
        if self.key == INF:
            return bytes()
        return self.key.to_bytes(32, "little")

    def dump_data(self, as_str=False):
        """
        Return json serialization for stored value.

        Parameters
        ----------
        as_str : bool, default False
            If True, return json serialization as str, otherwise as bytes.

        Returns
        -------
        bytes or str
            If as_str is True, return json serialization as str, otherwise as bytes.
        """
        res = json.dumps(self.val)
        if as_str:
            return res
        return res.encode("utf-8")

    def is_root(self) -> bool:
        """
        Check if node is a root.

        Returns
        -------
        bool
            Return True if node doesn't have parent, False otherwise.
        """
        return self.parent is None

    def is_child(self) -> bool:
        """
        Check if node is a child.

        Returns
        -------
        bool
            Return False if node doesn't have parent, True otherwise.
        """
        return not self.is_root()

    def is_left_child(self) -> bool:
        """
        Check if node is left child.

        Returns
        -------
        bool
            Return True if node has parent and it's left child is node, False otherwise.
        """
        return self.is_child() and self.parent.left is not None \
            and self.parent.left is self

    def is_right_child(self) -> bool:
        """
        Check if node is right child.

        Returns
        -------
        bool
            Return True if node has parent and it's right child is node, False otherwise.
        """
        return self.is_child() and self.parent.right is not None \
            and self.parent.right is self

    def get_sibling(self):
        """
        Get node's sibling (parent's other child).

        Returns
        -------
        Node or None
            Return node's sibling if it exists, None otherwise.
        """
        if self.is_root():
            return None
        if self.is_left_child():
            return self.parent.right
        else:
            return self.parent.left

    def get_grandparent(self):
        """
        Get node's grandparent (parent's parent).

        Returns
        -------
        Node or None
            Return node's grandparent if it exists, None otherwise.
        """
        if self.is_root() or self.parent.is_root():
            return None
        return self.parent.parent

    def get_uncle(self):
        """
        Get node's uncle (parent's sibling (parent's other child)).

        Returns
        -------
        Node or None
            Return node's uncle if it exists, None otherwise.
        """
        if self.is_root():
            return None
        return self.parent.get_sibling()

    def __str__(self, _indent="  ") -> str:
        """
        Return node's recursive string representation.
        Allows `print(self)` and `str(self)` syntaxes.

        Returns
        -------
        str
            Node's recursive string representation.
        """
        b = "()" if self.color != NIL else "[]"
        res = _indent[:-2] + " ⎣" + \
            "{} {}\n".format(b[0] + self.color[0] + b[1], self.key)
        if self.color != NIL:
            res += self.right.__str__(_indent + " |")
            res += self.left.__str__(_indent + "  ")
        return res

    def __getitem__(self, direction):
        """
        Return node's child by indexing.
        Allows `self[direction]` syntax to get the child.

        Parameters
        ----------
        direction : str, int or bool
            Determines whether to return left or right child.
            "L", 0 and False to return left child,
            any other input to return right child.

        Returns
        -------
        Node or None
            Node's selected child if it exists, None otherwise.
        """
        if direction in ["L", 0, False]:
            return self.left
        else:
            return self.right

    def __setitem__(self, direction, node) -> None:
        """
        Set node's child by indexing.
        Allows `self[direction] = node` syntax to set the child.

        Parameters
        ----------
        direction : str, int or bool
            Determines whether to set left or right child.
            "L", 0 and False to return left child,
            any other input to return right child.
        node : Node or None
            New value to replace selected child.
        """
        if direction in ["L", 0, False]:
            self.left = node
        else:
            self.right = node


class MRBT:
    """
    MRBT node.

    Parameters
    ----------
    hsh : func(lhs: bytes, rhs: bytes) -> bytes, optional
        Dual argument hash function for node Merkle augmentation.
    """

    def __init__(self, hsh=sha256_dual) -> None:
        self.root = Node(INF, NIL)
        if hsh is not None:
            def _calc_digest(node):
                if node.color != NIL:
                    lhs = node.left.digest
                    rhs = node.right.digest
                else:
                    lhs = (node.dump_data(), bytes())
                    rhs = (node.dump_key(), bytes())
                return (hsh(*lhs), hsh(*rhs))

            self._calc_digest = _calc_digest
        else:
            self._calc_digest = lambda x: (bytes(), bytes())
        self._update_digest(self.root)

    @classmethod
    def from_list(cls, lst, **kwargs):
        """
        Construct MRBT object from iterable.
        O(n log n).

        Parameters
        ----------
        lst : iterable
            Collection of keys or key, value pairs.
        **kwargs :
            Additional keywords passed to MRBT constructor.
        """
        res = cls(**kwargs)
        for it in lst:
            if isinstance(it, (int)):
                res.insert(it)
            else:
                res.insert(*it)
        return res

    @property
    def size(self) -> int:
        """
        O(1).

        int
            Number of stored keys.
        """
        return self.root.weight

    @property
    def digest(self) -> tuple:
        """
        O(1).

        tuple
            Root digest of the structure.
        """
        return self.root.digest

    def insert(self, key: int, val=None) -> None:
        """
        Insert new key if it doesn't exist.
        O(log n).

        Parameters
        ----------
        key : int
            Key to insert.
        val : optional
            Value to store by that key.
        """
        found, search_result = self._search(key, pair=True)
        if found:
            return

        focus = search_result[-1]
        direction = focus.is_left_child()

        insertion_leaf = Node(key, NIL, val=val)
        insertion_node = Node(key, parent=focus.parent,
                              left=insertion_leaf, right=focus)
        insertion_leaf.parent = insertion_node
        if focus.is_root():
            self.root = insertion_node
        else:
            focus.parent[1 - direction] = insertion_node
        focus.parent = insertion_node

        self._insert_fix(insertion_node)

    def delete(self, key: int) -> None:
        """
        Delete key if it exists.
        O(log n).

        Parameters
        ----------
        key : int
            Key to delete.
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
        Get value stored by the key.
        O(log n).

        Parameters
        ----------
        key : int
            Key to get value from.
        auth : bool, default False
            Return with verification object if True.

        Returns
        -------
        `val`, tuple
            Value stored by the key and it's verification object
            if auth is False and key exists.
        `val`
            Value stored by the key if auth is False and kay exists.
        None
            If key dosn't exist.
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

    def set(self, key: int, val=None) -> None:
        """
        Set value to store by the key if it exists.
        O(log n).

        Parameters
        ----------
        key : int
            Key to store the value by.
        val
            Value to store by that key.
        """
        found, search_result = self._search(key, pair=True)
        if not found:
            return
        focus = search_result[-1]
        focus.store(val)
        while focus is not None:
            self._update_digest(focus)
            focus = focus.parent

    def k_order(self, k) -> Node:
        """
        Get element by it's order.
        Supports negative indexation to search in reversed order.
        O(log n).

        Parameters
        ----------
        k : int
            Position of node to return.

        Returns
        -------
        Node or None
            Element with selected position if it's in range, None otherwise.
        """
        if k >= self.__len__() or k < -self.__len__():
            return None
        if k < 0:
            k = self.__len__() + k
        focus = self.root
        while focus.color != NIL:
            if k < focus[0].weight:
                focus = focus[0]
            else:
                k -= focus[0].weight
                focus = focus[1]
        return focus

    def compare(self, other) -> str:
        """
        Get symmetric difference with other object of the class in json str format.
        O(n + o).

        Parameters
        ----------
        other : MRBT

        Returns
        -------
        str
            Json representation of symmetric difference.

        Examples
        --------
        >>> a = MRBT.from_list([(1, "one"),
        ...                     (2, "two"),
        ...                     (5, "five")])
        >>> b = MRBT.from_list([(1, "one"),
        ...                     (2, "six")])
        >>> print(a.compare(b)) # indents are purposefully simplified
        [["Source", {key: 2, value: "\"two\""}],\
         ["Destination", {key: 2, value: "\"six\""}],\
         ["Source", {key: 5, value: "\"five\""}]]
        """
        res = []
        if not (self.__len__() or other.__len__()):
            return json.dumps(res)

        it1 = self.__iter__()
        it2 = other.__iter__()
        it1_node = next(it1)
        it2_node = next(it2)
        it1c = 0
        it2c = 0

        while it1c != -1 or it2c != -1:
            case = 0
            if it2c == -1:
                case = 0
            elif it2c == -1:
                case = 1
            elif it1_node.key < it2_node.key:
                case = 0
            elif it1_node.key > it2_node.key:
                case = 1
            elif it1_node.digest != it2_node.digest:
                case = 0
            else:
                case = 2

            if case == 0:
                res.append(["Source", {"key": it1_node.key,
                                       "value": it1_node.dump_data(as_str=True)}])
                it1c += 1
                it1_node = next(it1) if it1c < self.__len__() else None
            elif case == 1:
                res.append(["Destination", {"key": it2_node.key,
                                            "value": it2_node.dump_data(as_str=True)}])
                it2c += 1
                it2_node = next(it2) if it2c < other.__len__() else None
            else:
                it1c += 1
                it2c += 1
                it1_node = next(it1) if it1c < self.__len__() else None
                it2_node = next(it2) if it2c < other.__len__() else None
            if it1c >= self.__len__():
                it1c = -1
            if it2c >= other.__len__():
                it2c = -1
        return json.dumps(res)

    def __len__(self) -> int:
        """
        Get number of stored keys.
        Allows `len(self)` syntax.
        O(1).

        Returns
        -------
        int
            Number of stored keys.
        """
        return self.root.weight

    def __iter__(self) -> iter:
        """
        Get iterator for stored leaves.
        Allows `for x in self` syntax.
        DFS implementation, next element in
        O(log n) w.c., O(1) amortized.

        Returns
        -------
        iterator
            Yields leaf nodes by keys order.
        """
        focus = self.root
        from_left = True
        move = "D"
        while focus != None:
            if move == "D":
                if focus.color == NIL:
                    if focus.key == INF:
                        return
                    yield focus
                    move = "U"
                    from_left = focus.is_left_child()
                    focus = focus.parent
                else:
                    focus = focus[0]
                    move = "D"
            else:
                if from_left:
                    focus = focus[1]
                    move = "D"
                else:
                    move = "U"
                    from_left = focus.is_left_child()
                    focus = focus.parent

    def __contains__(self, key: int) -> bool:
        """
        Check if the key exists.
        O(log n).

        Parameters
        ----------
        key : int
            Key to check if exists.

        Returns
        -------
        bool
            True if key exists, False otherwise.
        """
        return self._search(key)[0]

    def __getitem__(self, key: int):
        """
        Get value stored by the key if it exists.
        Allows `self[key]` syntax.
        O(log n).

        Parameters
        ----------
        key : int
            Key to check stored value.

        Returns
        -------
        `val`, None
            Stored value if key exists, None otherwise.
        """
        return self.get(key)

    def __setitem__(self, key: int, val) -> None:
        """
        Set value stored by the key or insert it if key doesn't exist.
        Allows `self[key] = val` syntax.
        O(log n).

        Parameters
        ----------
        key : int
            Key to store value by.
        val
            Value to store by that key.
        """
        found, search_result = self._search(key, pair=True)
        if not found:
            return self.insert(key, val)
        focus = search_result[-1]
        focus.store(val)
        while focus is not None:
            self._update_digest(focus)
            focus = focus.parent

    def __eq__(self, other) -> bool:
        """
        Check if other object of the class has different root digest.
        A probabilistic way to compare if structures are equal.
        False positives are extremely rare with proper
        choice of hash function.
        Allows `self == other` syntax.
        O(1).

        Parameters
        ----------
        other : MRBT
            Other object to compare digests.
        """
        return self.root.digest == other.digest

    def __str__(self) -> str:
        """
        Return root node's recursive string representation.
        Allows `print(self)` and `str(self)` syntaxes.
        O(n).

        Returns
        -------
        str
            Root node's recursive string representation.
        """
        return self.root.__str__()

    def _update_digest(self, node: Node) -> None:
        if node.color != NIL:
            node.weight = node[0].weight + node[1].weight
        node.digest = self._calc_digest(node)

    def _search(self, key: int, pair=False):
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

    def _rotate(self, node: Node):
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

    def _insert_fix(self, focus: Node) -> None:
        self._update_digest(focus[0])

        while focus.is_child() and focus.parent.color == RED:
            P = focus.parent
            G = focus.get_grandparent()
            U = focus.get_uncle()
            if G is None:
                P.color = BLACK
                continue
            if U.color == RED:  # CASE 1
                P.color = BLACK
                U.color = BLACK
                G.color = RED
                self._update_digest(focus)
                self._update_digest(P)
                focus = G
                continue
            if focus.is_left_child() != focus.parent.is_left_child():  # CASE 2
                self._rotate(focus)
                focus = P
                continue
            else:  # CASE 3
                self._update_digest(focus)
                self._rotate(P)
                focus = G
                P.color = BLACK
                G.color = RED
                continue
        if self.root.color == RED:
            self.root.color = BLACK  # CASE 0

        while focus is not None:
            self._update_digest(focus)
            focus = focus.parent

    def _delete_fix(self, focus: Node, d_black=False) -> None:
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
                    self._update_digest(focus)
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
                    self._update_digest(S)
                    self._update_digest(Sc[1 - direction])
                    continue

        while focus is not None:
            self._update_digest(focus)
            focus = focus.parent

    def test(self) -> None:
        """
        Tests structure for:
            1. BST properties:
                - Correct keys ordering.
                - Linkage consistency.
                - Each node either leaf or has 2 children.
            2. RBT properties:
                - Black root.
                - Constant black depth.
                - Absence of red-red relationships.
            3. Merkle properties:
                - Digests consistency.
            4. Miscellaneous and given:
                - Correct subtree size statistics.
        O(n).
        """

        assert self.root.color != RED
        focus = self.root
        last_not_red = True
        from_left = True
        move = "D"
        bbalance = 0
        bbalance_leaf = -1
        while focus != None:
            if focus.color == NIL:
                assert focus[0] is None
                assert focus[1] is None
                assert focus.weight == 1 or focus.key == INF
            else:
                assert focus[0] is not None
                assert focus[1] is not None
                assert focus.weight == focus[0].weight + focus[1].weight
                assert focus[0].is_child()
                assert focus[1].is_child()
                assert focus[0].parent is focus
                assert focus[1].parent is focus
                assert focus[0].key <= focus.key
                assert focus[1].key > focus.key
            assert focus.is_child() or self.root is focus
            assert focus.digest == self._calc_digest(focus)
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
                    focus = focus[0]
                    move = "D"
            else:
                if last_not_red:
                    bbalance -= 1
                last_not_red = (focus.color != RED)
                if from_left:
                    focus = focus[1]
                    move = "D"
                else:
                    move = "U"
                    from_left = focus.is_left_child()
                    focus = focus.parent


def verify(t: MRBT, vo: tuple, hsh=sha256_dual):
    if t.digest != vo[0]:
        return False
    for i in range(len(vo) - 1, 0, -1):
        if hsh(*vo[i]) not in vo[i - 1]:
            return False
    return True
