# Red-Black Merkle Tree

An efficient authenticated data structure
based on generic Red-Black Tree with Merkle augmentation.

## Contents

- [Red-Black Merkle Tree](#red-black-merkle-tree)
  - [Contents](#contents)
  - [Theory](#theory)
  - [Usage](#usage)
    - [`MRBT` class](#mrbt-class)
      - [Constructors](#constructors)
      - [Attributes](#attributes)
      - [Methods](#methods)
    - [`verify` function](#verify-function)
  - [TODO](#todo)
  - [References](#references)

## Theory


| !["Red-Black Merkle Tree"](./_figures/fig1.png) |
| :---------------------------------------------: |
|    Red-Black Merkle Tree with fictive leaf.     |

See the [original implementation](#references) for basic understanding.

We added fictive leaf with infinity key to the original implementation. That way data structure acquires strict key bijection between internal nodes and leaves (each finite leaf has key of its closest ancestor in whose left subtree it lies).

Data is stored in finite keyed leaves of Red-Black Tree. Each node has also a pair of digests similar to Merkle trees for data
authentication.

## Usage

### `MRBT` class

#### Constructors

- `MRBT(hsh=sha256_dual)`
  - `hsh` is a function used for Merkle augmentation, takes 2 `bytes` objects and returns their combined hash `bytes`.
- `MRBT.from_list(lst, **kwargs)`
  - `lst` is iterable of either keys or key-value pairs for initial state.
  - `**kwargs` are additional keywords passed to original constructor (only `hsh` keyword supported yet).

#### Attributes

- `size`
  - Number of keys stored.
- `digest`
  - Root digest of the structure.

#### Methods

- `insert(key, val=None)`
  - Inserts `key` key with `val` value, `val` must be json-serializable. Ignores existing keys.
- `delete(key)`
  - Deletes `key` key from the storage. Ignores missing keys.
- `get(key, auth=False)`
  - Returns stored `key` key value if `auth` is false.
  - Returns pair of stored key value and verification object if `auth` is true.
  - Returns `None` if key is missing and `auth` is false.
  - Returns `None, None` pair if key is missing and `auth` is true.
- `set(key, val=None)`
  - Updates `key` key value with `val`, `val` must be json-serializable. Ignores missing keys.
- `k_order(k, as_str=True)`
  - List-alike indexing for `k`'th ordered `key` object, supports negatives for reversed order.
  - Returns `{'key': <key>, 'value': <value>}` `dict` if `as_str` is false, its json `str` otherwise.
  - Returns `None` if `k` is out of range.
- `compare(other, as_str=True)`
  - Returns comparison result over other `MRBT` object in `[[<target>, {'key': <key>, 'value': <value>}], ...]` `list` format if `as_str` is false, its json `str` otherwise.
    - `<target>` is either `'Source'` for `self` or `'Destination'` for `other`, `<key>` and `<value>` is a point of difference (either key is unique to the collection or values differ).
- `__len__()`
  - Allows `len(self)` for getting `size` attribute.
- `__iter__(as_str=True)`
  - Allows `for item in self` iterating. Yields `{'key': <key>, 'value': <value>}` `dict` objects if `as_str` is false, its json `str` otherwise.
- `__contains__()`
  - Allows `key in self` checks, returns `True` if `key` key exists, `False` otherwise.
- `__getitem__(key)`
  - Allows `self[key]` getting, returns `key` key stored value.
  - Returns `None` if key is missing.
- `__setitem__(key, val)`
  - Allows `self[key] = val` setting, updates `key` key value with `val` if key exists, inserts it otherwise, `val` must be json-serializable.
- `__eq__(other)`
  - Allows `self == other` morphism checks. False positive rate is controlled by hash function choice.
- `__str__(self)`
  - Allows `print(self)` printing for basic visualization.
- `test()`
  - Tests structure for BST, RBT and Merkle correctness. Returns error `str` message if failed, `None` otherwise.

### `verify` function

- `verify(t, vo, hsh=sha256_dual)`
  - Validation for verification object `vo`, trusted `MRBT` object `t` and same `hsh` dual argument hashing function. Returns `True` if validation passed, `False` otherwise.

## TODO

- Develop `test.py` for testing the structure.
- Clean the code up.

## References

- [1] Original Python 2 implementation:
  - [Red-Black Merkle Tree](https://github.com/amiller/redblackmerkle) - Andrew Miller (2012).
