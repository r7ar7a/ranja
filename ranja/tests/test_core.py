import os

import pytest

from ranja.core import update_dict_tree
from ranja import RanjaException
from ranja import KeyPolicy
from ranja import Configuration


EXISTENT = KeyPolicy.EXISTENT
NEW = KeyPolicy.NEW

def test_update_dict_tree_simple():
    assert {} == update_dict_tree({}, {})
    assert {'a': 2} == update_dict_tree({'a': 1}, {'a': 2})
    assert {'a': 2} == update_dict_tree({}, {'a': 2})
    assert {'a': 2} == update_dict_tree({'a': 2}, {})
    assert {'a': 1, 'b': 2} == update_dict_tree({'a': 1}, {'b': 2})

    assert {} == update_dict_tree({}, {}, key_policy=EXISTENT)
    assert {'a': 2} == update_dict_tree({'a': 1}, {'a': 2}, key_policy=EXISTENT)
    with pytest.raises(RanjaException):
        update_dict_tree({}, {'a': 2}, key_policy=EXISTENT)
    assert {'a': 2} == update_dict_tree({'a': 2}, {}, key_policy=EXISTENT)
    with pytest.raises(RanjaException):
        update_dict_tree({'a': 1}, {'b': 2}, key_policy=EXISTENT)

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

def test_Configuration_simple():
    cfg_string = '{a: 2, b: 3}'
    cfg = Configuration().add_yaml(cfg_string).resolve()
    assert cfg == {'a': 2, 'b': 3}

    cfg_string2 = '{a: [1, "2", 3], b: 3}'
    cfg2 = Configuration().add_yaml(cfg_string2).resolve()
    assert cfg2 == {'a': [1, '2', 3], 'b': 3}

def test_Configuration_policy_errors():
    with pytest.raises(RanjaException):
        Configuration().add_yaml('{a: 1}').add_yaml('{a: 1}', key_policy=NEW).resolve()

    with pytest.raises(RanjaException):
        Configuration().add_yaml('{a: 1}').add_yaml('{a: {b: 1}}').resolve()

    with pytest.raises(RanjaException):
        Configuration().add_yaml('{a: 1}').add_yaml('{b: 1}', key_policy=EXISTENT).resolve()

def test_Configuration_complex():
    cfg_defaults = (
        'a:\n'
        '  - 1\n'
        'b:\n'
        '  ba: 1\n'
        '  bb: {bba: \'{{a | jsonify}}\'}\n'
        'c: \'{{b.ba}}\'\n'
    )

    expected_cfg1 = {'a': [1], 'b': {'ba': 1, 'bb': {'bba': '[1]'}}, 'c': '1'}
    result_cfg1 = Configuration().add_yaml(cfg_defaults).resolve()
    assert expected_cfg1 == result_cfg1

    cfg_spec = '{b: {ba: 32}}'
    expected_cfg2 = {'a': [1], 'b': {'ba': 32, 'bb': {'bba': '[1]'}}, 'c': '32'}
    result_cfg2 = (
        Configuration()
        .add_yaml(cfg_defaults)
        .add_yaml(cfg_spec, key_policy=EXISTENT)
        .resolve())
    assert expected_cfg2 == result_cfg2

def test_Configuration_escaping():
    cfg_apostrophe = (
        'a: don\'t do it\n'
        'b: \'{{a | esc_a}}\'\n')
    assert ({'a': "don't do it", 'b': "don't do it"} ==
            Configuration().add_yaml(cfg_apostrophe).resolve())

    cfg_multiline = (
        'a: |-\n'
        '  x\n'
        '  y\n'
        'b: |-\n'
        '  {{a | indent(2)}}\n')
    assert ({'a': 'x\ny', 'b': 'x\ny'} ==
            Configuration().add_yaml(cfg_multiline).resolve())

def test_Configuration_os_env():
    os.environ['SOME_ENV_VARIABLE'] = 'value'
    assert (Configuration()
            .add_yaml('x: \'{{"SOME_ENV_VARIABLE" | os_env}}\'')
            .resolve() == {'x': 'value'})
    assert (Configuration()
            .add_yaml('x: \'{{"SOME_ENV_VARIABLE" | os_env_strict}}\'')
            .resolve() == {'x': 'value'})
    assert (Configuration()
            .add_yaml('x: \'{{"NOT_ENV_VARIABLE" | os_env}}\'')
            .resolve() == {'x': 'None'})
    with pytest.raises(KeyError):
        assert (Configuration()
                .add_yaml('x: \'{{"NOT_ENV_VARIABLE" | os_env_strict}}\'')
                .resolve())

def test_stop_condition():
    cfg_no_variable = (
        'x: \n'
        '# {%- for i in range(10) %}\n'
        '  - a \n'
        '# {%- endfor %}\n')
    assert Configuration().add_yaml(cfg_no_variable).resolve() == {
        'x': ['a' for _ in range(10)]
    }

def test_os_environ():
    cfg_string = '{a: 2, b: 3, c: {x: 1, y: 2}}'
    os.environ['RANJA_b'] = '4'
    os.environ['RANJA_c__x'] = 'alma'
    cfg = Configuration().add_yaml(cfg_string).add_env_var_prefix('RANJA_').resolve()
    assert cfg == {'a': 2, 'b': '4', 'c': {'x': 'alma', 'y': 2}}
