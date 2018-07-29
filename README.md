# Ranja

Loads yaml configuration files with support of jinja2 substitution.

## Basic features

### One can use the variables defined in the same file.
`default.yml`:
```yaml
folders:
  project_root: '/path/to/project/root'
  data_dir: '{{folders.project_root}}/data/'

data_files:
  important_data: '{{folders.data_dir}}/important_data.json'
  other_important_data: '{{folders.data_dir}}/other_important_data.json'

database_host: '54.36.126.1'
```

```python
from ranja import Configuration
cfg = Configuration().add_path('default.yml').resolve()
```

### One can redifine variables in a separated config file.
`my_config.yml`:
```yaml
folders:
  data_dir: '/home/myself/data/project'

database_host: '127.0.0.1'
```

```python
from ranja import Configuration, KeyPolicy
cfg = (Configuration()
       .add_path('default.yml')
       .add_path('my_config.yml', key_policy=KeyPolicy.EXISTENT)
       .resolve())
```
Here with the key policy "EXISTENT", an error is thrown whenever a configuration parameter is present in `my_config.yml` but not defined in `default.yml`.

### One can set the config parameters using environment variables
```bash
PROJ_database_host=127.0.0.1 PROJ_folders__data_dir=/home/myself/data/project python << 'PY_SCRIPT'
from ranja import Configuration, KeyPolicy
cfg = (Configuration()
       .add_path('default.yml')
       .add_env_var_prefix(('PROJ_', key_policy=KeyPolicy.EXISTENT)
       .resolve())
PY_SCRIPT
```

### Basicly one can use all the features of jinja2.
Ranja does nothing but recursively loads and replaces the given configuration files on themselves while it finds anything to be replaced. Be aware that at any moment the used configurations should be both a valid yaml file and a valid jinja template.

If the jinja2 environment is set to be able to load configs from the filesystem, one can use include blocks as well.
`my_config.yml`:
```yaml
# Loads the content of default.yml
# {{"\n"}}{% include 'default.yml' %}
--- # needs to use a separated part if the included yaml file contains the database_host key
database_host: '127.0.0.1'
```
```python
from ranja import Configuration
from jinja2 import FileSystemLoader
cfg = Configuration()
cfg.get_jinja_env().loader = FileSystemLoader('.')
cfg.add_yaml(my).resolve()
```

This one below is a working example, but if you do things like this, you probably write code in a template language instead of a regular programming language.
`my_config2.yml`:
```yaml
services:
  s1:
    workers: 4
    name: s1
  s2:
    workers: 6
    name: s2
---
list_of_numbers:
# {% for i in range(10) %}
  - '{{i | int}}'
# {% endfor %}

# {% if scale_x is defined %}
# {% for service_name, service_config in services.items() %}
# {{'\n'}}---
# {{'\n'}}services:
# {{'\n'}}  {{service_name}}:
# {{'\n'}}    workers: {{scale_x | int * service_config.workers | int}}
# {% endfor %}
# {% endif%}
```


