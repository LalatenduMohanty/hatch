from __future__ import annotations

import types
from unittest.mock import patch

import pytest

from hatchling.plugin.manager import ClassRegister, HookRegistry, PluginManager, ThirdPartyPlugins


class TestPluginManagerIntegration:
    """End-to-end tests proving the stdlib-only HookRegistry replaces pluggy correctly."""

    @pytest.mark.parametrize(
        ("plugin_type", "expected_names"),
        [
            ("builder", {"wheel", "sdist", "app", "binary", "custom"}),
            ("build_hook", {"custom", "version"}),
            ("version_source", {"code", "env", "regex"}),
            ("version_scheme", {"standard"}),
            ("metadata_hook", {"custom"}),
        ],
    )
    def test_resolves_builtin_plugins(self, plugin_type, expected_names):
        pm = PluginManager()
        classes = getattr(pm, plugin_type).collect(include_third_party=False)

        assert set(classes.keys()) == expected_names
        for name, cls in classes.items():
            assert name == cls.PLUGIN_NAME

    def test_get_returns_class_by_name(self):
        pm = PluginManager()

        wheel_cls = pm.builder.get("wheel")
        assert wheel_cls is not None
        assert wheel_cls.PLUGIN_NAME == "wheel"


class TestThirdPartyPluginsLoad:
    def test_loads_module_entry_point(self):
        module = types.ModuleType("fake_plugin")
        module.hatch_register_builder = lambda: "from_ep"

        class FakeEntryPoint:
            name = "fake"
            group = "hatch"

            def load(self):
                return module

        registry = HookRegistry()
        third_party = ThirdPartyPlugins(registry)

        with patch("importlib.metadata.entry_points", return_value=[FakeEntryPoint()]):
            third_party.load()

        assert third_party.loaded is True
        assert registry.call_hook("hatch_register_builder") == ["from_ep"]

    def test_loads_callable_entry_point(self):
        def hatch_register_builder():
            return "from_callable_ep"

        class FakeEntryPoint:
            name = "fake"
            group = "hatch"

            def load(self):
                return hatch_register_builder

        registry = HookRegistry()
        third_party = ThirdPartyPlugins(registry)

        with patch("importlib.metadata.entry_points", return_value=[FakeEntryPoint()]):
            third_party.load()

        assert third_party.loaded is True
        assert registry.call_hook("hatch_register_builder") == ["from_callable_ep"]

    def test_get_falls_through_to_third_party(self):
        class ThirdPartyPlugin:
            PLUGIN_NAME = "external"

        registry = HookRegistry()
        third_party = ThirdPartyPlugins(registry)

        def fake_load():
            registry.register_hook("hatch_register_builder", lambda: ThirdPartyPlugin)
            third_party.loaded = True

        third_party.load = fake_load

        register = ClassRegister(lambda: registry.call_hook("hatch_register_builder"), "PLUGIN_NAME", third_party)
        result = register.get("external")

        assert result is ThirdPartyPlugin
        assert third_party.loaded is True
