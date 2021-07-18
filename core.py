"""
MRBT (Red-Black Merkle Tree)
---------
An efficient authenticated data structure
based on generic Red-Black Tree with Merkle augmentation.

Original Python 2 implementation:
    Andrew Miller.
    https://github.com/amiller/redblackmerkle

General TODO:
    1. Clean the code up.
    2. Decide whether code should raise exceptions.
    3. Typing corrections.
"""


__all__ = ["MRBT", "verify"]

import json
from math import inf as INF

RED = "RED"
BLACK = "BLACK"
NIL = "NIL"


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
    val : object, default None
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
        self.shortcut = None
        if self.color == NIL:
            self.next = None
            self.prev = None
        if self.color == NIL and self.key != INF:
            self.val = val
            self.weight = 1

    def dump_key(self) -> bytes:
        """
        Return bytes representation of node's key.

        Returns
        -------
        bytes
            Bytes representation of node's key.
        """
        if self.key == INF:
            return bytes()
        return self.key.to_bytes(32, "big", signed=True)

    def dump_data(self, as_json: bool = False):
        """
        Return json serialization for stored value.

        Parameters
        ----------
        as_json : bool, default False
            If True, return json serialization as str, otherwise as bytes.

        Returns
        -------
        bytes
            Value bytes json object if as_json is False.
        str
            Value str json object if as_json is True.
        """
        res = json.dumps(self.val)
        if as_json:
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
        if self.parent is None:
            return False
        if self.parent.left is None:
            return False
        return self.parent.left is self

    def is_right_child(self) -> bool:
        """
        Check if node is right child.

        Returns
        -------
        bool
            Return True if node has parent and it's right child is node, False otherwise.
        """
        if self.parent is None:
            return False
        if self.parent.right is None:
            return False
        return self.parent.right is self

    def get_sibling(self):
        """
        Get node's sibling (parent's other child).

        Returns
        -------
        Node
            Node's sibling if it exists.
        None
            If sibling doesn't exist.
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
        Node
            Node's grandparent if it exists
        None
            If grandparent doesn't exist.
        """
        if self.is_root() or self.parent.is_root():
            return None
        return self.parent.parent

    def get_uncle(self):
        """
        Get node's uncle (parent's sibling (parent's other child)).

        Returns
        -------
        Node
            Node's uncle if it exists.
        None
            If uncle doesn't exist.
        """
        if self.is_root():
            return None
        return self.parent.get_sibling()

    def __str__(self, _indent: str = "  ") -> str:
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
        Node
            Node's selected child if it exists.
        None
            If selecter child doesn't exits.
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
    hsh : str or func(lhs: bytes, rhs: bytes) -> bytes, default "sha256"
        Name of hashlib function (either of "sha1", "sha224", "sha256", "sha384", "sha512",
        "blake2b" or "blake2s") or custom dual argument hash function
        for node Merkle augmentation. Unrecognized names default to "sha256".
    """

    def __init__(self, hsh="sha256") -> None:
        self._root = Node(INF, NIL)
        if isinstance(hsh, str):
            if hsh == "sha1":
                from hashlib import sha1
                func = sha1
            elif hsh == "sha224":
                from hashlib import sha224
                func = sha224
            elif hsh == "sha384":
                from hashlib import sha384
                func = sha384
            elif hsh == "sha512":
                from hashlib import sha512
                func = sha512
            elif hsh == "blake2b":
                from hashlib import blake2b
                func = blake2b
            elif hsh == "blake2s":
                from hashlib import blake2s
                func = blake2s
            else:
                from hashlib import sha256
                func = sha256

            def hsh(x, y): return func(x + y).digest()

        def _calc_digest(node):
            if node.color != NIL:
                lhs = node[0].digest
                rhs = node[1].digest
            else:
                lhs = (node.dump_data(), bytes())
                rhs = (node.dump_key(), bytes())
            return (hsh(*lhs), hsh(*rhs))

        self._calc_digest = _calc_digest
        self._update_digest(self._root)

    @classmethod
    def from_iter(cls, itr, **kwargs):
        """
        Construct MRBT object from iterable.
        O(n log n).

        Parameters
        ----------
        itr : iterable
            Collection of keys or key-value pairs.
        **kwargs :
            Additional keywords passed to MRBT constructor.
        """
        res = cls(**kwargs)
        for it in itr:
            if isinstance(it, (int)):
                res.insert(it)
            else:
                res.insert(*it)
        return res

    @classmethod
    def from_dict(cls, dct: dict, **kwargs):
        """
        Construct MRBT object from key-value dict object.
        O(n log n).

        Parameters
        ----------
        dct : dict
            Key-value dict object.
        **kwargs :
            Additional keywords passed to MRBT constructor.
        """
        res = cls(**kwargs)
        for it in dct.items():
            res.insert(*it)
        return res

    @property
    def size(self) -> int:
        """
        O(1).

        int
            Number of stored keys.
        """
        return self._root.weight

    @property
    def digest(self) -> tuple:
        """
        O(1).

        tuple
            Root digest of the structure.
        """
        return self._root.digest

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
        found, search_result = self._search(key)
        if found:
            return

        focus = search_result
        direction = focus.is_left_child()

        insertion_leaf = Node(key, NIL, val=val)
        insertion_node = Node(key, parent=focus.parent,
                              left=insertion_leaf, right=focus)
        insertion_node.shortcut = insertion_leaf
        insertion_leaf.shortcut = insertion_node
        insertion_leaf.parent = insertion_node
        insertion_leaf.prev = focus.prev
        insertion_leaf.next = focus
        focus.prev = insertion_leaf
        if insertion_leaf.prev is not None:
            insertion_leaf.prev.next = insertion_leaf
        if focus.is_root():
            self._root = insertion_node
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
        found, search_result = self._search(key)
        if not found:
            return

        focus = search_result.shortcut
        if focus.prev is not None:
            focus.prev.next = focus.next
        focus.next.prev = focus.prev
        search_result.key = focus.parent.key
        search_result.shortcut = focus.parent.shortcut
        search_result.shortcut.shortcut = search_result

        parent = focus.parent
        sibling = focus.get_sibling()

        d_black = (parent.color != RED) and (sibling.color != RED)

        if parent.is_root():
            self._root = sibling
        else:
            direction_1 = parent.is_left_child()
            parent.parent[1 - direction_1] = sibling
        sibling.parent = parent.parent

        if sibling.color == RED:
            sibling.color = BLACK

        self._delete_fix(sibling, d_black)

    def get(self, key: int, verified: bool = False):
        """
        Get value stored by the key.
        O(log n).

        Parameters
        ----------
        key : int
            Key to get value from.
        verified : bool, default False
            Return with verification object if True.

        Returns
        -------
        object, tuple
            Value stored by the key and it's verification object
            if verified is True and key exists.
        None, None
            If key doesn't exist and verified is True.
        object
            Value stored by the key if verified is False and key exists.
        None
            If key doesn't exist and verified is False.
        """
        found, search_result = self._search(key)
        if not found:
            if verified:
                return None, None
            return None

        focus = search_result.shortcut

        if not verified:
            return focus.val

        vo = []
        val = focus.val
        while focus is not None:
            vo.append(focus.digest)
            focus = focus.parent
        return val, tuple(vo)

    def set(self, key: int, val=None) -> None:
        """
        Set value stored by the key or insert it if key doesn't exist.
        O(log n).

        Parameters
        ----------
        key : int
            Key to store the value by.
        val : object, default None
            Value to store by that key, must be json-serializable.
        """
        found, search_result = self._search(key)
        if not found:
            return self.insert(key, val)

        focus = search_result.shortcut

        focus.val = val
        while focus is not None:
            self._update_digest(focus)
            focus = focus.parent

    def by_keys_order(self, k: int, as_json: bool = False):
        """
        Get element by it's order.
        Supports negative indexation to search in reversed order.
        O(log n).

        Parameters
        ----------
        k : int
            Position of node to return.
        as_json : bool, default False
            Whether to return json object or string.

        Returns
        -------
        dict
            Key-value dict json object if as_json is False.
        str
            Key-value str json object if as_json is True.
        None
            If order is out of range.

        Examples
        --------
        >>> a = MRBT.from_iter([(1, "one"),
        ...                     (4, "four"),
        ...                     (5, "five")])
        >>> print(a.k_order(2, as_json=False))
        {"key": 4, "value": "four"}
        """
        if k >= self.__len__() or k < -self.__len__():
            return None
        if k < 0:
            k = self.__len__() + k
        focus = self._root
        while focus.color != NIL:
            if k < focus[0].weight:
                focus = focus[0]
            else:
                k -= focus[0].weight
                focus = focus[1]
        res = {"key": focus.key, "value": focus.val}
        if as_json:
            return json.dumps(res)
        return res

    def get_change_set(self, other, as_json: bool = False):
        """
        Get symmetric difference with other object of the class in json format.
        !!! Relies on digests in order to skip equal subtrees.
        ... False positive equals are extremely rare with proper
        ... choice of hash function.
        ... Correctness of return value is not guaranteed.
        O(n + o) w.c., O(k log n) for k << n insertions / deletions / modifications.

        Parameters
        ----------
        other : MRBT
            Object of a class for comparison.
        as_json : bool, default False
            Whether to return json object or string.

        Returns
        -------
        list
            Symmetric difference list json object if as_json is False.
        str
            Symmetric difference str json object if as_json is False

        Examples
        --------
        >>> a = MRBT.from_iter([(1, "one"),
        ...                     (2, "two"),
        ...                     (5, "five")])
        >>> b = MRBT.from_iter([(1, "one"),
        ...                     (2, "six")])
        >>> print(a.compare(b, as_json=False))
        [["Destination", {"key": 2, "value": "six"}],
         ["Source", {"key": 2, "value": "two"}],
         ["Source", {"key": 5, "value": "five"}]]
        """
        focus = [self._root, other._root]
        for i in range(2):
            while focus[i][0] is not None:
                focus[i] = focus[i][0]
            focus[i] = focus[i].parent

        res = []

        def _next(target, skip=False):
            nonlocal focus
            if skip:
                while focus[target].is_right_child():
                    focus[target] = focus[target].parent
                focus[target] = focus[target].parent
            else:
                focus[target] = focus[target].shortcut.next.shortcut

        def _write(target):
            nonlocal focus
            res.append(["Destination" if target else "Source",
                        {"key": focus[target].shortcut.key,
                         "value": focus[target].shortcut.val}])

        while not (focus[0] is None and focus[1] is None):
            if focus[1] is None:
                _write(0)
                _next(0)
            elif focus[0] is None:
                _write(1)
                _next(1)
            elif focus[0].key != focus[1].key:
                target = int(focus[0].key > focus[1].key)
                _write(target)
                _next(target)
            else:
                if focus[0].shortcut.digest != focus[1].shortcut.digest:
                    _write(0)
                    _write(1)
                cut_allowed = (focus[0].digest[1] == focus[1].digest[1])
                _next(0, skip=cut_allowed)
                _next(1, skip=cut_allowed)

        if as_json:
            return json.dumps(res)
        return res

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
        return self._root.weight

    def __iter__(self, as_json: bool = False) -> iter:
        """
        Iterator for stored leaves.
        Allows `for x in self` syntax.
        DFS implementation, next element in
        O(1).

        Parameters
        ----------
        as_json : bool, default False
            Whether to return json object or string.

        Yields
        ------
        str
            Key-value str json object of next element in order if as_json is True.
        dict
            Key-value dict json object of next element in order if as_json is False.

        Examples
        --------
        >>> a = MRBT.from_iter([(1, "one"),
        ...                     (4, "four"),
        ...                     (5, "five")])
        >>> for item in a:
        ...     print("found:", item)
        found: {'key': 1, 'value': 'one'}
        found: {'key': 4, 'value': 'four'}
        found: {'key': 5, 'value': 'five'}
        """
        iterator = self._iter()
        node = next(iterator)
        while node is not None:
            res = {"key": node.key, "value": node.val}
            if as_json:
                yield json.dumps(res)
            else:
                yield res
            node = next(iterator)
        return

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
        object
            Stored value if key exists.
        None
            If key doesn't exits.
        """
        return self.get(key)

    def __setitem__(self, key: int, val) -> None:
        """
        Set value stored by the key or insert it if key doesn't exist.
        Allows `self[key] = val` syntax.
        `set` method analogue.
        O(log n).

        Parameters
        ----------
        key : int
            Key to store value by.
        val : object
            Value to store by that key, must be json-serializable.
        """
        self.set(key, val)

    def __eq__(self, other) -> bool:
        """
        Check if other object of the class has different root digest.
        !!! A probabilistic way to compare if structures are equal.
        ... False positives are extremely rare with proper
        ... choice of hash function.
        Allows `self == other` syntax.
        O(1).

        Parameters
        ----------
        other : MRBT
            Other object to compare digests.

        Returns
        -------
        bool
            True if root digest are equal, False otherwise.
        """
        return self._root.digest == other.digest

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
        return self._root.__str__()

    def _iter(self):
        focus = self._root
        while focus[0] is not None:
            focus = focus[0]
        while focus.key != INF:
            yield focus
            focus = focus.next
        yield None
        return

    def _update_digest(self, node: Node) -> None:
        if node.color != NIL:
            node.weight = node[0].weight + node[1].weight
        node.digest = self._calc_digest(node)

    def _search(self, key: int):
        focus = self._root
        while focus.color != NIL:
            if key == focus.key:
                return True, focus
            if key < focus.key:
                focus = focus[0]
            elif key > focus.key:
                focus = focus[1]
        return False, focus

    def _rotate(self, node: Node):
        direction = node.is_left_child()
        parent = node.parent
        subtree = node[direction] if node.color != NIL else None

        if parent.is_root():
            self._root = node
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
        if self._root.color == RED:
            self._root.color = BLACK  # CASE 0

        while focus is not None:
            self._update_digest(focus)
            focus = focus.parent

    def _delete_fix(self, focus: Node, d_black: bool = False) -> None:
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

    def _get_change_set__legacy(self, other, as_json: bool = False):
        """
        Exact O(n + o) implementation.
        """
        res = []
        iterator = [["Source", self._iter()],
                    ["Destination", other._iter()]]
        nodes = [next(iterator[0][1]), next(iterator[1][1])]
        while nodes[0] is not None or nodes[1] is not None:
            direction = -1
            if nodes[0] is None:
                nodes[0], nodes[1] = nodes[1], nodes[0]
                iterator[0], iterator[1] = iterator[1], iterator[0]
            if nodes[1] is None:
                direction = 0
            elif nodes[0].key < nodes[1].key:
                direction = 0
            elif nodes[0].key > nodes[1].key:
                direction = 1
            elif nodes[0].digest != nodes[1].digest:
                direction = 1
            if direction == -1:
                nodes = [next(iterator[0][1]), next(iterator[1][1])]
            else:
                res.append([iterator[direction][0],
                            {"key": nodes[direction].key,
                             "value": nodes[direction].val}])
                nodes[direction] = next(iterator[direction][1])
        if as_json:
            return json.dumps(res)
        return res

    def _test(self):
        """
        Test structure for:
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
            4. Miscellaneous:
                - Correct subtree size statistics.
                - Shortcut consistency.
                - Doubly linked list consistency.
        O(n).

        Returns
        -------
        str
            Message if a problem has been encountered.
        None
            If structure test passed.
        """
        if self._root.color == RED:
            return "Root is red."
        focus = self._root
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
                elif focus.color == NIL:
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
                if focus.digest != self._calc_digest(focus):
                    return "Digests are wrong."
                if focus.color != RED:
                    bbalance += 1
                else:
                    if not last_not_red:
                        return "Red-red relationship."
                last_not_red = (focus.color != RED)
                if focus.color == NIL:
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
                last_not_red = (focus.color != RED)
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


def verify(t: MRBT, vo: tuple, hsh="sha256"):
    """
    Validate verification object

    Parameters
    ----------
    t : MRBT
        Trusted structure.
    vo : tuple
        Verification object.
    hsh : str or func(lhs: bytes, rhs: bytes) -> bytes, default "sha256"
        Name of hashlib function (either of "sha1", "sha224", "sha256", "sha384", "sha512",
        "blake2b" or "blake2s") or custom dual argument hash function
        for node Merkle augmentation. Unrecognized names default to "sha256". Should be same
        as in original tree.

    Returns
    -------
    bool
        True if validation succeeded, False otherwise.
    """
    if isinstance(hsh, str):
        if hsh == "sha1":
            from hashlib import sha1
            func = sha1
        elif hsh == "sha224":
            from hashlib import sha224
            func = sha224
        elif hsh == "sha384":
            from hashlib import sha384
            func = sha384
        elif hsh == "sha512":
            from hashlib import sha512
            func = sha512
        elif hsh == "blake2b":
            from hashlib import blake2b
            func = blake2b
        elif hsh == "blake2s":
            from hashlib import blake2s
            func = blake2s
        else:
            from hashlib import sha256
            func = sha256

        def hsh(x, y): return func(x + y).digest()

    if t.digest != vo[-1]:
        return False
    for i in range(len(vo) - 1):
        if hsh(*vo[i]) not in vo[i + 1]:
            return False
    return True
