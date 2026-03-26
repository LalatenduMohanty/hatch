from __future__ import annotations

import importlib.metadata
import inspect
from functools import partial
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: dict[str, list[Callable]] = {}
        self._registered: list[object] = []

    def add_hookspecs(self, module: object) -> None:
        """No-op kept for API compatibility.

        Hooks are discovered by naming convention (hatch_register_*)
        rather than explicit specification registration.
        """

    def register(self, module_or_obj: object) -> None:
        if any(obj is module_or_obj for obj in self._registered):
            return
        self._registered.append(module_or_obj)

        def predicate(member):
            return inspect.isfunction(member) or inspect.ismethod(member)

        for name, obj in inspect.getmembers(module_or_obj, predicate):
            if name.startswith("hatch_register_"):
                self._hooks.setdefault(name, []).append(obj)

    def register_hook(self, name: str, func: Callable) -> None:
        hooks = self._hooks.setdefault(name, [])
        if func not in hooks:
            hooks.append(func)

    def call_hook(self, name: str) -> list:
        results = []
        for func in self._hooks.get(name, []):
            result = func()
            if result is not None:
                results.append(result)
        return results


class PluginManager:
    def __init__(self) -> None:
        self.manager = HookRegistry()
        self.third_party_plugins = ThirdPartyPlugins(self.manager)
        self.initialized = False

    def initialize(self) -> None:
        """Override point for subclasses (e.g. hatch frontend PluginManager)."""

    def __getattr__(self, name: str) -> ClassRegister:
        if not self.initialized:
            self.initialize()
            self.initialized = True

        hook_name = f"hatch_register_{name}"
        # Cannot use getattr() here: if hook_name doesn't exist as a method,
        # getattr() would call __getattr__ again, causing infinite recursion.
        for cls in type(self).__mro__:
            if hook_name in cls.__dict__:
                cls.__dict__[hook_name](self)
                break

        register = ClassRegister(partial(self.manager.call_hook, hook_name), "PLUGIN_NAME", self.third_party_plugins)
        setattr(self, name, register)
        return register

    def hatch_register_version_source(self) -> None:
        from hatchling.version.source.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_version_scheme(self) -> None:
        from hatchling.version.scheme.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_builder(self) -> None:
        from hatchling.builders.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_build_hook(self) -> None:
        from hatchling.builders.hooks.plugin import hooks

        self.manager.register(hooks)

    def hatch_register_metadata_hook(self) -> None:
        from hatchling.metadata.plugin import hooks

        self.manager.register(hooks)


class ClassRegister:
    def __init__(self, registration_method: Callable, identifier: str, third_party_plugins: ThirdPartyPlugins) -> None:
        self.registration_method = registration_method
        self.identifier = identifier
        self.third_party_plugins = third_party_plugins

    def collect(self, *, include_third_party: bool = True) -> dict:
        if include_third_party and not self.third_party_plugins.loaded:
            self.third_party_plugins.load()

        classes: dict[str, type] = {}

        for raw_registered_classes in self.registration_method():
            registered_classes = (
                raw_registered_classes if isinstance(raw_registered_classes, list) else [raw_registered_classes]
            )
            for registered_class in registered_classes:
                name = getattr(registered_class, self.identifier, None)
                if not name:  # no cov
                    message = f"Class `{registered_class.__name__}` does not have a {name} attribute."
                    raise ValueError(message)

                if name in classes:  # no cov
                    message = (
                        f"Class `{registered_class.__name__}` defines its name as `{name}` but "
                        f"that name is already used by `{classes[name].__name__}`."
                    )
                    raise ValueError(message)

                classes[name] = registered_class

        return classes

    def get(self, name: str) -> type | None:
        if not self.third_party_plugins.loaded:
            classes = self.collect(include_third_party=False)
            if name in classes:
                return classes[name]

        return self.collect().get(name)


class ThirdPartyPlugins:
    def __init__(self, manager: HookRegistry) -> None:
        self.manager = manager
        self.loaded = False

    def load(self) -> None:
        for ep in importlib.metadata.entry_points(group="hatch"):
            plugin = ep.load()
            name = getattr(plugin, "__name__", "")
            if callable(plugin) and name.startswith("hatch_register_"):
                self.manager.register_hook(name, plugin)
            else:
                self.manager.register(plugin)
        self.loaded = True


PluginManagerBound = TypeVar("PluginManagerBound", bound=PluginManager)
