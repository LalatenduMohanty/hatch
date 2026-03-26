# Plugins

-----

Hatch utilizes a convention-based plugin system that relies only on the Python standard library. Plugins are discovered through [entry points](https://packaging.python.org/en/latest/specifications/entry-points/) and hooks are identified by naming convention — any callable whose name starts with `hatch_register_` is automatically registered.

## Overview

All plugins provide registration hooks that return one or more classes that inherit from a particular [type](#types) interface.

Each registration hook must be a callable named `hatch_register_<plugin_type>`. For example, if you wanted to create a new kind of environment you could do:

```python tab="hooks.py"
from .plugin import SpecialEnvironment


def hatch_register_environment():
    return SpecialEnvironment
```

!!! note
    The `@hookimpl` decorator from `hatchling.plugin` is still available but is a no-op retained
    solely for backward compatibility. You do **not** need to import or use it — naming your
    function `hatch_register_*` is all that is required for discovery. Existing plugins that
    use `@hookimpl` will continue to work without any changes.

The hooks can return a single class or a list of classes.

Every class must define an attribute called `PLUGIN_NAME` that users will select when they wish to use the plugin. So in the example above, the class might be defined like:

```python tab="plugin.py"
...
class SpecialEnvironment(...):
    PLUGIN_NAME = 'special'
    ...
```

## Project configuration

### Naming

It is recommended that plugin project names are prefixed with `hatch-`. For example, if you wanted to make a plugin that provides some functionality for a product named `foo` you might do:

```toml tab="pyproject.toml"
[project]
name = "hatch-foo"
```

### Discovery

You'll need to define your project as a [Python plugin](../config/metadata.md#plugins) for Hatch:

```toml tab="pyproject.toml"
[project.entry-points.hatch]
foo = "pkg.hooks"
```

The name of the plugin should be the project name (excluding any `hatch-` prefix) and the path should represent the module that contains the registration hooks.

### Classifier

Add [`Framework :: Hatch`](https://pypi.org/search/?c=Framework+%3A%3A+Hatch) to your project's [classifiers](../config/metadata.md#classifiers) to make it easy to search for Hatch plugins:

```toml tab="pyproject.toml"
[project]
classifiers = [
  ...
  "Framework :: Hatch",
  ...
]
```

## Types

### Hatchling

These are all involved in building projects and therefore any defined dependencies are automatically installed in each build environment.

- [Builder](builder/reference.md)
- [Build hook](build-hook/reference.md)
- [Metadata hook](metadata-hook/reference.md)
- [Version source](version-source/reference.md)
- [Version scheme](version-scheme/reference.md)

### Hatch

These must be installed in the same environment as Hatch itself.

- [Environment](environment/reference.md)
- [Environment collector](environment-collector/reference.md)
- [Publisher](publisher/reference.md)
