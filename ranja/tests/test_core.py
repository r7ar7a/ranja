import pytest

from ranja.core import update_dict_tree
from ranja.core import RanjaException
from ranja.core import KeyPolicy

EXISTENT = KeyPolicy.EXISTENT
NEW = KeyPolicy.NEW

def test_update_dict_tree_simple():
  assert {} == update_dict_tree({}, {})
  assert {'a': 2} == update_dict_tree({'a': 1}, {'a': 2})
  assert {'a': 2} == update_dict_tree({}, {'a': 2})
  assert {'a': 2} == update_dict_tree({'a': 2}, {})
  assert {'a': 1, 'b': 2} == update_dict_tree({'a': 1}, {'b':2})

  assert {} == update_dict_tree({}, {}, key_policy=EXISTENT)
  assert {'a': 2} == update_dict_tree({'a': 1}, {'a': 2}, key_policy=EXISTENT)
  with pytest.raises(RanjaException):
    update_dict_tree({}, {'a': 2}, key_policy=EXISTENT)
  assert {'a': 2} == update_dict_tree({'a': 2}, {}, key_policy=EXISTENT)
  with pytest.raises(RanjaException):
    update_dict_tree({'a': 1}, {'b':2}, key_policy=EXISTENT)

  assert {} == update_dict_tree({}, {}, key_policy=NEW)
  with pytest.raises(RanjaException):
    update_dict_tree({'a': 1}, {'a': 2}, key_policy=NEW)
  assert {'a': 2} == update_dict_tree({}, {'a': 2}, key_policy=NEW)
  assert {'a': 2} == update_dict_tree({'a': 2}, {}, key_policy=NEW)
  assert (
      {'a': 1, 'b': 2} ==
      update_dict_tree({'a': 1}, {'b': 2}, key_policy=NEW))

  with pytest.raises(RanjaException):
    update_dict_tree({'a': {'b': 1}}, {'a': 2})

  with pytest.raises(RanjaException):
    update_dict_tree({'a': 2}, {'a': {'b': 1}})

def test_update_dict_tree_complex():
  a = {1: {2: 11, 3: 12}, 4: 13}
  b = {1: {2: 21}, 5: {6: 22}}
  res = {1: {2: 21, 3: 12}, 4: 13, 5: {6: 22}}
  assert a is update_dict_tree(a, b)
  assert res == update_dict_tree(a, b)
