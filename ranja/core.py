import os
import json
from enum import Enum

import yaml
from jinja2 import Environment, StrictUndefined


KeyPolicy = Enum('KeyPolicy', [
    'EXISTENT',  # only existent keys are allowed
    'NEW',  # only non-existent keys are allowed
    'ANY',
])


class Configuration():
    def __init__(self):
        self._jinja_env = Environment(undefined=StrictUndefined)
        self._jinja_env.filters['jsonify'] = json.dumps
        self._jinja_env.filters['esc_a'] = lambda s: s.replace("'", "''")
        self._jinja_env.filters['os_env'] = os.environ.get
        self._jinja_env.filters['os_env_strict'] = os.environ.__getitem__

        self._conf_parts = []
        self._dict = {}
        self._resolved = False

    def get_jinja_env(self):
        return self._jinja_env

    def add_yaml(self, yaml_string, key_policy=KeyPolicy.ANY):
        self._conf_parts.append({'yaml_string': yaml_string, 'key_policy': key_policy})
        return self

    def add_path(self, yaml_path, key_policy=KeyPolicy.ANY):
        with open(yaml_path) as yaml_file:
            return self.add_yaml(yaml_file.read(), key_policy=key_policy)

    def add_dict_tree(self, dict_tree, key_policy=KeyPolicy.ANY):
        self._conf_parts.append({'dict_tree': dict_tree, 'key_policy': key_policy})
        return self

    def add_env_var_prefix(self, env_var_prefix, key_policy=KeyPolicy.ANY):
        return self.add_dict_tree(read_os_env_tree(env_var_prefix), key_policy=key_policy)

    def resolve(self, os_env_prefix=None):
        if self._resolved:
            raise RanjaException("Already resolved.")
        self._resolved = True

        self._update_tree()
        while self._check_templates():
            self._update_yamls()
            self._update_tree()
        return self._dict

    def _update_tree(self):
        self._dict = {}
        for conf_part in self._conf_parts:
            if 'dict_tree' in conf_part:
                dict_trees = [conf_part['dict_tree']]
            if 'yaml_string' in conf_part:
                dict_trees = yaml.safe_load_all(conf_part['yaml_string'])
            for dict_tree in dict_trees:
                update_dict_tree(self._dict, dict_tree, key_policy=conf_part['key_policy'])


    def _update_yamls(self):
        for conf_part in self._conf_parts:
            if 'yaml_string' in conf_part:
                template = self._jinja_env.from_string(conf_part['yaml_string'])
                conf_part['yaml_string'] = template.render(self._dict)

    def _check_templates(self):
        return any(
            (self._jinja_env.block_start_string in conf_part['yaml_string']) or
            (self._jinja_env.variable_start_string in conf_part['yaml_string'])
            for conf_part in self._conf_parts
            if 'yaml_string' in conf_part)


class RanjaException(Exception):
    pass


def read_os_env_tree(prefix):
    dict_from_environ = {
        k[len(prefix):]: v for k, v in os.environ.items()
        if k.startswith(prefix)}

    result = {}
    for k, v in dict_from_environ.items():
        place = result
        for key_path_part in k.split('__')[:-1]:
            if key_path_part not in place:
                place[key_path_part] = {}
            place = place[key_path_part]
        place[k.split('__')[-1]] = v
    return result


def update_dict_tree(dt1, dt2, key_policy=KeyPolicy.ANY):
    for key in dt2:
        if (key in dt1 and
                isinstance(dt1[key], dict) and
                isinstance(dt2[key], dict)):
            update_dict_tree(dt1[key], dt2[key], key_policy)
        else:
            if key in dt1 and (isinstance(dt1[key], dict) or isinstance(dt2[key], dict)):
                raise RanjaException(
                    "ERROR: Only one of {} and {} is a dict.".format(dt1[key], dt2[key]))
            if key_policy == KeyPolicy.EXISTENT and key not in dt1:
                raise RanjaException(
                    "ERROR: KeyPolicy.EXISTENT forbids new key ({})".format(key))
            if key_policy == KeyPolicy.NEW and key in dt1:
                raise RanjaException(
                    "ERROR: KeyPolicy.NEW forbids existent key ({})".format(key))
            dt1[key] = dt2[key]
    return dt1
