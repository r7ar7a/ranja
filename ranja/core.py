import os
import json
import yaml
from enum import Enum
from jinja2 import Environment, StrictUndefined


KeyPolicy = Enum('KeyPolicy', [
    'EXISTENT',  # only existent keys are allowed
    'NEW',  # only non-existent keys are allowed
    'ANY',
  ])

def read_os_env_tree(prefix):
  dict_from_environ = {k[len(prefix):]: v for k, v in os.environ.items()
      if k.startswith(prefix)}

  result = {}
  for k, v in dict_from_environ.items():
    place = result
    for key_path_part in k.split('.')[:-1]:
      if key_path_part not in place:
        place[key_path_part] = {}
      place = place[key_path_part]
    place[k.split('.')[-1]] = v
  return result


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
            "ERROR: KeyPolicy.EXISTENT forbids new key ({})".format(key))
      if key_policy == KeyPolicy.NEW and key in d1:
        raise RanjaException(
            "ERROR: KeyPolicy.NEW forbids existent key ({})".format(key))
      d1[key] = d2[key]
  return d1

class Configuration(object):
  def __init__(self):
    self._jinja_env = Environment(undefined=StrictUndefined)
    self._jinja_env.filters['jsonify'] = json.dumps
    self._jinja_env.filters['esc_a'] = lambda s: s.replace("'", "''")

    self._conf_parts = []
    self._dict = {}
    self._os_dict = {}
    self._resolved = False

  def get_jinja_env(self):
    return self._jinja_env

  def add(self, yaml_string, key_policy=KeyPolicy.ANY):
    self._conf_parts.append(
        {'yaml_string': yaml_string, 'key_policy': key_policy})
    return self

  def resolve(self, os_env_prefix=None):
    if self._resolved:
      raise RanjaException(
          "Already resolved.".format(key))
    self._resolved = True

    if os_env_prefix is not None:
      self._os_dict = read_os_env_tree(os_env_prefix)

    self._update_tree()
    while self._check_templates():
      self._update_yamls()
      self._update_tree()
    return self._dict

  def _update_tree(self):
    self._dict = {}
    for conf_part in self._conf_parts:
      update_dict_tree(self._dict,
          yaml.load(conf_part['yaml_string']),
          key_policy=conf_part['key_policy'])
    update_dict_tree(self._dict, self._os_dict, key_policy=KeyPolicy.EXISTENT)


  def _update_yamls(self):
    for conf_part in self._conf_parts:
      template = self._jinja_env.from_string(conf_part['yaml_string'])
      conf_part['yaml_string'] = template.render(self._dict)

  def _check_templates(self):
    return any(conf_part['yaml_string'].find('{{') >= 0
        for conf_part in self._conf_parts)


class RanjaException(Exception):
  pass
