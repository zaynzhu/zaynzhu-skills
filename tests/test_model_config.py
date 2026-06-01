"""Tests for model_config.py — YAML parser, serializer, and value parsing.

Tests only pure functions. No API calls, no interactive input.
"""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent.parent / "skills" / "model-router" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from model_config import parse_yaml_simple, _parse_value, yaml_to_str, _format_val


class TestParseValue(unittest.TestCase):
    """Test _parse_value for all value types."""

    def test_null_variants(self):
        self.assertIsNone(_parse_value("null"))
        self.assertIsNone(_parse_value("None"))
        self.assertIsNone(_parse_value("~"))

    def test_bool_variants(self):
        self.assertTrue(_parse_value("true"))
        self.assertTrue(_parse_value("True"))
        self.assertFalse(_parse_value("false"))
        self.assertFalse(_parse_value("False"))

    def test_int(self):
        self.assertEqual(_parse_value("42"), 42)
        self.assertEqual(_parse_value("0"), 0)
        self.assertEqual(_parse_value("-1"), -1)

    def test_float(self):
        self.assertEqual(_parse_value("3.14"), 3.14)
        self.assertEqual(_parse_value("0.1"), 0.1)
        self.assertEqual(_parse_value("-2.5"), -2.5)

    def test_inline_array(self):
        self.assertEqual(_parse_value("[a, b, c]"), ["a", "b", "c"])
        self.assertEqual(_parse_value("[gpt4o, claude-sonnet]"), ["gpt4o", "claude-sonnet"])
        self.assertEqual(_parse_value("[]"), [])

    def test_quoted_string(self):
        self.assertEqual(_parse_value('"hello world"'), "hello world")
        self.assertEqual(_parse_value("'hello world'"), "hello world")

    def test_plain_string(self):
        self.assertEqual(_parse_value("hello"), "hello")
        self.assertEqual(_parse_value("openai"), "openai")

    def test_string_with_special_chars(self):
        # Strings with # or : should be handled (quoted vs unquoted)
        self.assertEqual(_parse_value('"http://example.com"'), "http://example.com")


class TestParseYamlSimple(unittest.TestCase):
    """Test parse_yaml_simple with various YAML structures."""

    def test_flat_key_value(self):
        text = "name: test\nvalue: 42\nflag: true"
        result = parse_yaml_simple(text)
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["value"], 42)
        self.assertTrue(result["flag"])

    def test_nested_dict(self):
        text = "models:\n  gpt4o:\n    provider: openai\n    model: gpt-4o"
        result = parse_yaml_simple(text)
        self.assertEqual(result["models"]["gpt4o"]["provider"], "openai")
        self.assertEqual(result["models"]["gpt4o"]["model"], "gpt-4o")

    def test_inline_array(self):
        text = "participants: [gpt4o, claude, gemini]"
        result = parse_yaml_simple(text)
        self.assertEqual(result["participants"], ["gpt4o", "claude", "gemini"])

    def test_list_items(self):
        text = "items:\n  - a\n  - b\n  - c"
        result = parse_yaml_simple(text)
        self.assertEqual(result["items"], ["a", "b", "c"])

    def test_list_of_dicts(self):
        text = (
            "routing:\n"
            "  - match: quick_task\n"
            "    prefer: [gpt4o]\n"
            "  - match: complex_reasoning\n"
            "    prefer: [claude-opus]"
        )
        result = parse_yaml_simple(text)
        self.assertEqual(len(result["routing"]), 2)
        self.assertEqual(result["routing"][0]["match"], "quick_task")
        self.assertEqual(result["routing"][0]["prefer"], ["gpt4o"])
        self.assertEqual(result["routing"][1]["match"], "complex_reasoning")

    def test_null_value(self):
        text = "api_key_env: null"
        result = parse_yaml_simple(text)
        self.assertIsNone(result["api_key_env"])

    def test_comments_skipped(self):
        text = "# This is a comment\nname: test\n# Another comment\nvalue: 42"
        result = parse_yaml_simple(text)
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["value"], 42)
        self.assertNotIn("#", result)

    def test_empty_lines_skipped(self):
        text = "name: test\n\n\nvalue: 42"
        result = parse_yaml_simple(text)
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["value"], 42)

    def test_complex_config(self):
        """Test with the actual model-router.yaml structure."""
        text = """profiles:
  gpt4o:
    provider: openai
    model: gpt-4o
    api_key_env: OPENAI_API_KEY
    capabilities: [text, image]
    endpoint: "https://api.openai.com/v1/chat/completions"
    max_tokens: 4096
    cost:
      input_per_1m: 2.5
      output_per_1m: 10.0
routing:
  - match: has_image_input
    prefer: [gpt4o, gemini-vision]
    cost_mode: cheapest"""
        result = parse_yaml_simple(text)
        self.assertIn("profiles", result)
        self.assertIn("gpt4o", result["profiles"])
        self.assertEqual(result["profiles"]["gpt4o"]["provider"], "openai")
        self.assertEqual(result["profiles"]["gpt4o"]["cost"]["input_per_1m"], 2.5)
        self.assertEqual(result["routing"][0]["match"], "has_image_input")

    def test_model_debate_yaml_structure(self):
        """Test with the actual model-debate.yaml structure."""
        text = """models:
  gpt4o:
    provider: openai
    model: gpt-4o
    api_key_env: OPENAI_API_KEY
    endpoint: https://api.openai.com/v1/chat/completions
    max_tokens: 4096

  claude-sonnet:
    provider: anthropic
    model: claude-sonnet-4-6
    api_key_env: ANTHROPIC_API_KEY
    endpoint: https://api.anthropic.com/v1/messages
    max_tokens: 4096

debate:
  participants: [gpt4o, claude-sonnet]
  default_mode: single
  max_rounds: 3
  convergence_ratio: 0.8"""
        result = parse_yaml_simple(text)
        self.assertIn("models", result)
        self.assertIn("gpt4o", result["models"])
        self.assertIn("claude-sonnet", result["models"])
        self.assertEqual(result["debate"]["default_mode"], "single")
        self.assertEqual(result["debate"]["max_rounds"], 3)
        self.assertEqual(result["debate"]["convergence_ratio"], 0.8)


class TestYamlToStr(unittest.TestCase):
    """Test yaml_to_str serialization."""

    def test_flat_dict(self):
        data = {"name": "test", "value": 42}
        result = yaml_to_str(data)
        self.assertIn("name: test", result)
        self.assertIn("value: 42", result)

    def test_nested_dict(self):
        data = {"models": {"gpt4o": {"provider": "openai"}}}
        result = yaml_to_str(data)
        self.assertIn("models:", result)
        self.assertIn("gpt4o:", result)
        self.assertIn("provider: openai", result)

    def test_list_inline(self):
        data = {"participants": ["a", "b", "c"]}
        result = yaml_to_str(data)
        self.assertIn("participants: [a, b, c]", result)

    def test_null_value(self):
        data = {"key": None}
        result = yaml_to_str(data)
        self.assertIn("key: null", result)

    def test_bool_value(self):
        data = {"flag": True, "other": False}
        result = yaml_to_str(data)
        self.assertIn("flag: true", result)
        self.assertIn("other: false", result)

    def test_format_val_special_chars(self):
        """Strings with # or : should be quoted."""
        self.assertEqual(_format_val("http://example.com"), '"http://example.com"')
        self.assertEqual(_format_val("value # comment"), '"value # comment"')


class TestYamlRoundtrip(unittest.TestCase):
    """Test that parse -> serialize -> parse preserves structure."""

    def test_roundtrip_router_config(self):
        original = {
            "profiles": {
                "gpt4o": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "api_key_env": "OPENAI_API_KEY",
                    "capabilities": ["text", "image"],
                    "endpoint": "https://api.openai.com/v1/chat/completions",
                    "max_tokens": 4096,
                    "cost": {"input_per_1m": 2.5, "output_per_1m": 10.0},
                }
            },
            "routing": [
                {"match": "quick_task", "prefer": ["gpt4o"], "cost_mode": "cheapest"}
            ],
        }
        yaml_str = yaml_to_str(original)
        parsed = parse_yaml_simple(yaml_str)

        self.assertEqual(parsed["profiles"]["gpt4o"]["provider"], "openai")
        self.assertEqual(parsed["profiles"]["gpt4o"]["model"], "gpt-4o")
        self.assertEqual(parsed["profiles"]["gpt4o"]["max_tokens"], 4096)
        self.assertEqual(parsed["routing"][0]["match"], "quick_task")
        self.assertEqual(parsed["routing"][0]["cost_mode"], "cheapest")


if __name__ == "__main__":
    unittest.main()
