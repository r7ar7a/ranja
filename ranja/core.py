from enum import Enum


KeyPolicy = Enum('KeyPolicy', [
    'EXISTENT',  # only existent keys are allowed
    'NEW',  # only non-existent keys are allowed
    'ANY'
  ])

def update_dict_tree(d1, d2, key_policy=KeyPolicy.ANY):
  for key in d2:
    if (key in d1 and
        isinstance(d1[key], dict) and
        isinstance(d2[key], dict)):
      update_dict_tree(d1[key], d2[key], key_policy)
    else:
      if key in d1 and (isinstance(d1[key], dict) or isinstance(d2[key], dict)):
        raise RanjaException(
            "ERROR: Only one of {} and {} is a dict.".format(d1[key], d2[key]))
      if key_policy == KeyPolicy.EXISTENT and key not in d1:
        raise RanjaException(
            "ERROR: KeyPolicy.EXISTENT forbids new key_policy({})".format(key))
      if key_policy == KeyPolicy.NEW and key in d1:
        raise RanjaException(
            "ERROR: KeyPolicy.NEW forbids existent key_policy({})".format(key))
      d1[key] = d2[key]
  return d1


class RanjaException(Exception):
  pass
  