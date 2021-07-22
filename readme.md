# Red-Black Merkle Tree

An efficient authenticated data structure
based on generic Red-Black Tree with Merkle augmentation.

## Contents

- [Red-Black Merkle Tree](#red-black-merkle-tree)
  - [Contents](#contents)
  - [Theory](#theory)
  - [Requirements](#requirements)
  - [Usage](#usage)
    - [`MRBT` class](#mrbt-class)
      - [Constructors](#constructors)
      - [Attributes](#attributes)
      - [Methods](#methods)
    - [`verify` function](#verify-function)
  - [Testing](#testing)
  - [TODO](#todo)
  - [References](#references)

## Theory

|                                   !["Red-Black Merkle Tree"](./_figures/fig1.png)                                    |
| :------------------------------------------------------------------------------------------------------------------: |
| Red-Black Merkle Tree with fictive leaf and verification object example<br>(concatenation as dual argument hashing). |

See the [original implementation](#references) for basic understanding.

We added fictive leaf with infinity key to the original implementation.
This way, data structure acquires strict key bijection between internal nodes and leaves:
each finite leaf has key of its closest ancestor in whose left subtree it lies and
each internal node has key of largest key in its left subtree.

Data is stored in finite keyed leaves of Red-Black Tree.
Each node has also a pair of digests similar to Merkle trees for data authentication.

Additionally, leaves were linked with corresponding internal nodes and
tied in doubly linked list for more efficient operations execution and
better iteration over stored data.

Merkle augmentation helps to identify equal subtrees which used
in efficient difference estimation of similar structures.

## Requirements

- `pytest >= 6.2.4`
- `blake3 >= 0.2.0`
- `python_version >= '3.7'`

## Usage

### [`MRBT` class][1]

#### Constructors

- [`MRBT(hsh='sha256')`][2]
  - `hsh` is `str` name of base `hashlib` function
    (either of `'sha1'`, `'sha224'`, `'sha256'`, `'sha384'`, `'sha512'`, `'blake2b'` or `'blake2s'`)
    or custom function that takes 2 `bytes` objects and returns their combined hash `bytes`,
    used for Merkle augmentation.
- [`MRBT.from_iter(itr, **kwargs)`][3]
  - `itr` is iterable of either keys (for `None` values) or key-value pairs for initial state,
    keys must be `int` and values must be json-serializable.
  - `**kwargs` are additional keywords passed to original constructor
    (only `hsh` keyword supported yet).
- [`MRBT.from_dict(dct, **kwargs)`][4]
  - `dct` is a key-value `dict` object, keys must be `int` and values must be json-serializable.
  - `**kwargs` are additional keywords passed to original constructor
    (only `hsh` keyword supported yet).

#### Attributes

- [`size`][5]
  - Number of keys stored.
- [`digest`][6]
  - Root digest of the structure.

#### Methods

- [`insert(key, val=None)`][7]
  - Inserts `key` key with `val` value, `val` must be json-serializable. Ignores existing keys.
- [`delete(key)`][8]
  - Deletes `key` key from the storage. Ignores missing keys.
- [`get(key, verified=False)`][9]
  - Returns stored `key` key value if `verified` is false.
  - Returns pair of stored key value and verification object if `verified` is true.
  - Returns `None` if key is missing and `verified` is false.
  - Returns `None, None` pair if key is missing and `verified` is true.
- [`set(key, val=None)`][10]
  - Updates `key` key value with `val` if key exists, inserts it otherwise,
    `val` must be json-serializable.
- [`by_keys_order(k, as_json=False)`][11]
  - List-alike indexing for `k`'th ordered `key` object, supports negatives for reversed order.
  - Returns `{'key': <key>, 'value': <value>}` `dict` if `as_json` is false,
    its json `str` otherwise.
  - Returns `None` if `k` is out of range.
- [`get_change_set(other, as_json=False)`][12]
  - Returns comparison result over `other` `MRBT` object in
    `[[<target>, {'key': <key>, 'value': <value>}], ...]` `list` format if `as_json` is false,
    its json `str` otherwise.
    `<target>` is either `'Source'` for `self` or `'Destination'` for `other`,
    `<key>` and `<value>` is a point of difference
    (either key is unique to the collection or values differ).
  - **!!!** Incorrect results rate is controlled by hash function choice.
- [`__len__()`][13]
  - Allows `len(self)` for getting `size` attribute.
- [`__iter__(as_json=False)`][14]
  - Allows `for item in self` iterating. Yields `{'key': <key>, 'value': <value>}` `dict` objects
    if `as_json` is false, its json `str` otherwise.
- [`__contains__()`][15]
  - Allows `key in self` checks, returns `True` if `key` key exists, `False` otherwise.
- [`__getitem__(key)`][16]
  - Allows `self[key]` getting, returns `key` key stored value.
  - Returns `None` if key is missing.
- [`__setitem__(key, val)`][17]
  - Allows `self[key] = val` setting, updates `key` key value with `val` if key exists,
    inserts it otherwise, `val` must be json-serializable.
  - `set` method analogue.
- [`__eq__(other)`][18]
  - Allows `self == other` probabilistic morphism checks.
  - **!!!** False positive rate is controlled by hash function choice.
- [`__str__(self)`][19]
  - Allows `print(self)` printing for basic visualization.

### [`verify` function][20]

- [`verify(trusted_digest, vo, hsh='sha256')`][21]
  - Validation for verification object `vo`, trusted structure `tuple` digest `trusted_digest` and
    same `hsh` option that was passed to `MRBT` constructor. Returns `True` if validation passed,
    `False` otherwise.

## Testing

- `pytest >= 6.2.4` is required.
- Done with `pytest -q test.py` command.

## TODO

- Clean the code up.

## References

- \[1\] Original Python 2 implementation:
  - [Red-Black Merkle Tree](https://github.com/amiller/redblackmerkle) - Andrew Miller (2012).

[1]:  https://github.com/Tsekho/MRBT/blob/main/core.py#L272-L972   "MRBT class"
[2]:  https://github.com/Tsekho/MRBT/blob/main/core.py#L284-L327   "MRBT.__init__"
[3]:  https://github.com/Tsekho/MRBT/blob/main/core.py#L329-L348   "MRBT.from_iter"
[4]:  https://github.com/Tsekho/MRBT/blob/main/core.py#L350-L366   "MRBT.from_dict"
[5]:  https://github.com/Tsekho/MRBT/blob/main/core.py#L368-L376   "MRBT.size"
[6]:  https://github.com/Tsekho/MRBT/blob/main/core.py#L378-L386   "MRBT.digest"
[7]:  https://github.com/Tsekho/MRBT/blob/main/core.py#L388-L424   "MRBT.insert"
[8]:  https://github.com/Tsekho/MRBT/blob/main/core.py#L426-L463   "MRBT.delete"
[9]:  https://github.com/Tsekho/MRBT/blob/main/core.py#L465-L505   "MRBT.get"
[10]: https://github.com/Tsekho/MRBT/blob/main/core.py#L507-L528   "MRBT.set"
[11]: https://github.com/Tsekho/MRBT/blob/main/core.py#L530-L574   "MRBT.by_keys_order"
[12]: https://github.com/Tsekho/MRBT/blob/main/core.py#L576-L660   "MRBT.get_change_set"
[13]: https://github.com/Tsekho/MRBT/blob/main/core.py#L662-L673   "MRBT.__len__"
[14]: https://github.com/Tsekho/MRBT/blob/main/core.py#L675-L714   "MRBT.__iter__"
[15]: https://github.com/Tsekho/MRBT/blob/main/core.py#L716-L731   "MRBT.__contains__"
[16]: https://github.com/Tsekho/MRBT/blob/main/core.py#L733-L751   "MRBT.__getitem__"
[17]: https://github.com/Tsekho/MRBT/blob/main/core.py#L753-L767   "MRBT.__setitem__"
[18]: https://github.com/Tsekho/MRBT/blob/main/core.py#L769-L788   "MRBT.__eq__"
[19]: https://github.com/Tsekho/MRBT/blob/main/core.py#L790-L801   "MRBT.__str__"

[20]: https://github.com/Tsekho/MRBT/blob/main/core.py#L975-L1030 "verify function"
[21]: https://github.com/Tsekho/MRBT/blob/main/core.py#L975-L1030 "verify"
