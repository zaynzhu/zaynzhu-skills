from __future__ import annotations

import sqlite3
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from adapters.hermes import register


class FakeContext:
    def __init__(self):
        self.hooks = {}
        self.tools = {}
        self.unload_callbacks = []

    def get_config(self, key, default=None):
        if key == "timezone":
            return "Asia/Shanghai"
        if key == "retention_days":
            return "invalid"
        return default

    def register_hook(self, name, handler):
        self.hooks[name] = handler

    def register_tool(self, *, name, handler, **_):
        self.tools[name] = handler

    def on_unload(self, callback):
        self.unload_callbacks.append(callback)


class PluginRegistrationTests(unittest.TestCase):
    def test_registers_public_hook_and_tools_with_invalid_optional_config(self) -> None:
        plugins_module = types.ModuleType("plugins")
        storage_module = types.ModuleType("plugins.plugin_storage")
        storage_module.plugin_db = lambda _: sqlite3.connect(":memory:", check_same_thread=False)
        context = FakeContext()
        with patch.dict(
            sys.modules,
            {
                "plugins": plugins_module,
                "plugins.plugin_storage": storage_module,
            },
        ):
            register(context)

        self.assertEqual(set(context.hooks), {"pre_llm_call"})
        self.assertEqual(
            set(context.tools),
            {"timeline_resolve", "timeline_query", "timeline_revise", "timeline_forget"},
        )
        self.assertEqual(len(context.unload_callbacks), 1)
        context.unload_callbacks[0]()


if __name__ == "__main__":
    unittest.main()
