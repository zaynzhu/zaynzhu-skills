"""Tests for model_debate.py — request building, response parsing, output formatting, state memory.

Tests only pure functions. No API calls, no interactive input.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent.parent / "skills" / "model-debate" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from model_debate import (
    build_request,
    extract_response,
    format_single_output,
    format_multi_output,
    save_last_models,
    load_last_models,
    init_config,
    save_config,
    PROTOCOL_TEMPLATES,
    SERVICE_PRESETS,
    RETRYABLE_STATUS,
)


class TestBuildRequest(unittest.TestCase):
    """Test API request construction for all providers."""

    def test_openai(self):
        cfg = {
            "provider": "openai",
            "model": "gpt-4o",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "api_key_env": "TEST_KEY",
            "max_tokens": 4096,
        }
        msgs = [{"role": "user", "content": "Hello"}]
        with patch.dict(os.environ, {"TEST_KEY": "sk-test123"}):
            endpoint, headers, body = build_request(cfg, msgs)

        self.assertEqual(endpoint, cfg["endpoint"])
        self.assertIn("Bearer sk-test123", headers["Authorization"])
        body_json = json.loads(body)
        self.assertEqual(body_json["model"], "gpt-4o")
        self.assertEqual(body_json["messages"], msgs)
        self.assertEqual(body_json["max_tokens"], 4096)

    def test_anthropic(self):
        cfg = {
            "provider": "anthropic",
            "model": "claude-sonnet-4-6",
            "endpoint": "https://api.anthropic.com/v1/messages",
            "api_key_env": "TEST_KEY",
            "max_tokens": 4096,
        }
        msgs = [{"role": "user", "content": "Hello"}]
        with patch.dict(os.environ, {"TEST_KEY": "sk-ant-abc"}):
            endpoint, headers, body = build_request(cfg, msgs)

        self.assertEqual(headers["x-api-key"], "sk-ant-abc")
        self.assertEqual(headers["anthropic-version"], "2023-06-01")
        body_json = json.loads(body)
        self.assertEqual(body_json["model"], "claude-sonnet-4-6")

    def test_google(self):
        cfg = {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "api_key_env": "TEST_KEY",
            "max_tokens": 4096,
        }
        msgs = [{"role": "user", "content": "Hello"}]
        with patch.dict(os.environ, {"TEST_KEY": "google-key"}):
            endpoint, headers, body = build_request(cfg, msgs)

        self.assertIn("key=google-key", endpoint)
        body_json = json.loads(body)
        self.assertIn("contents", body_json)
        # Google converts role: user -> user, assistant -> model
        self.assertEqual(body_json["contents"][0]["role"], "user")

    def test_google_assistant_role_mapping(self):
        cfg = {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "api_key_env": "TEST_KEY",
        }
        msgs = [{"role": "assistant", "content": "Previous answer"}]
        with patch.dict(os.environ, {"TEST_KEY": "key"}):
            _, _, body = build_request(cfg, msgs)

        body_json = json.loads(body)
        self.assertEqual(body_json["contents"][0]["role"], "model")

    def test_ollama(self):
        cfg = {
            "provider": "ollama",
            "model": "llava",
            "endpoint": "http://localhost:11434/api/generate",
        }
        msgs = [{"role": "user", "content": "Hello"}]
        _, headers, body = build_request(cfg, msgs)

        body_json = json.loads(body)
        self.assertEqual(body_json["model"], "llava")
        self.assertEqual(body_json["prompt"], "Hello")
        self.assertFalse(body_json["stream"])

    def test_ollama_uses_last_message(self):
        cfg = {"provider": "ollama", "model": "llama3", "endpoint": "http://localhost:11434/api/generate"}
        msgs = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "last message"},
        ]
        _, _, body = build_request(cfg, msgs)
        body_json = json.loads(body)
        self.assertEqual(body_json["prompt"], "last message")

    def test_generic_provider(self):
        cfg = {
            "provider": "custom",
            "model": "my-model",
            "endpoint": "https://custom.api.com/v1/chat",
            "api_key_env": "CUSTOM_KEY",
        }
        msgs = [{"role": "user", "content": "Hello"}]
        with patch.dict(os.environ, {"CUSTOM_KEY": "secret"}):
            _, headers, body = build_request(cfg, msgs)

        self.assertIn("Bearer secret", headers["Authorization"])
        body_json = json.loads(body)
        self.assertEqual(body_json["model"], "my-model")

    def test_missing_api_key_env(self):
        cfg = {
            "provider": "openai",
            "model": "gpt-4o",
            "endpoint": "https://api.openai.com/v1/chat/completions",
        }
        msgs = [{"role": "user", "content": "Hello"}]
        # No api_key_env set — should use empty string
        with patch.dict(os.environ, {}, clear=True):
            _, headers, body = build_request(cfg, msgs)
        self.assertIn("Bearer ", headers["Authorization"])


class TestExtractResponse(unittest.TestCase):
    """Test response parsing for all providers."""

    def test_openai(self):
        resp = {"choices": [{"message": {"content": "Hello world"}}]}
        self.assertEqual(extract_response("openai", resp), "Hello world")

    def test_openai_empty_choices(self):
        """Empty choices list should return '', not crash."""
        resp = {"choices": []}
        self.assertEqual(extract_response("openai", resp), "")

    def test_openai_none_element(self):
        resp = {"choices": [None]}
        self.assertEqual(extract_response("openai", resp), "")

    def test_anthropic_empty_content(self):
        resp = {"content": []}
        self.assertEqual(extract_response("anthropic", resp), "")

    def test_anthropic_none_element(self):
        resp = {"content": [None]}
        self.assertEqual(extract_response("anthropic", resp), "")

    def test_google_empty_candidates(self):
        resp = {"candidates": []}
        self.assertEqual(extract_response("google", resp), "")

    def test_google_empty_parts(self):
        resp = {"candidates": [{"content": {"parts": []}}]}
        self.assertEqual(extract_response("google", resp), "")

    def test_google_none_element(self):
        resp = {"candidates": [None]}
        self.assertEqual(extract_response("google", resp), "")

    def test_anthropic(self):
        resp = {"content": [{"text": "Hello from Claude"}]}
        self.assertEqual(extract_response("anthropic", resp), "Hello from Claude")

    def test_google(self):
        resp = {"candidates": [{"content": {"parts": [{"text": "Hello from Gemini"}]}}]}
        self.assertEqual(extract_response("google", resp), "Hello from Gemini")

    def test_ollama(self):
        resp = {"response": "Hello from Ollama"}
        self.assertEqual(extract_response("ollama", resp), "Hello from Ollama")

    def test_unknown_provider_returns_json(self):
        resp = {"result": "some data"}
        result = extract_response("unknown", resp)
        self.assertIn("some data", result)


class TestFormatOutput(unittest.TestCase):
    """Test output formatting functions."""

    def test_format_single_output(self):
        answers = {"model1": "answer1", "model2": "answer2"}
        consensus = "## 共识结论\n综合回答"
        output = format_single_output(answers, consensus)

        self.assertIn("## 共识结论", output)
        self.assertIn("综合回答", output)
        self.assertIn("## 各模型原始回答", output)
        self.assertIn("### model1", output)
        self.assertIn("answer1", output)
        self.assertIn("### model2", output)
        self.assertIn("answer2", output)

    def test_format_multi_output(self):
        all_rounds = [
            {"m1": "r1a1", "m2": "r1a2"},
            {"m1": "r2a1", "m2": "r2a2"},
        ]
        consensus = "共识"
        output = format_multi_output(all_rounds, consensus)

        self.assertIn("共识", output)
        self.assertIn("第 1 轮（独立回答）", output)
        self.assertIn("第 2 轮", output)
        self.assertIn("r1a1", output)
        self.assertIn("r2a1", output)

    def test_format_single_empty_answers(self):
        output = format_single_output({}, "no consensus")
        self.assertIn("no consensus", output)
        self.assertIn("## 各模型原始回答", output)


class TestStateMemory(unittest.TestCase):
    """Test save/load last models state persistence."""

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / ".state.json"
            with patch("model_debate.STATE_PATH", state_path):
                save_last_models(["gpt4o", "claude"], "single")
                models, mode = load_last_models()
            self.assertEqual(models, ["gpt4o", "claude"])
            self.assertEqual(mode, "single")

    def test_load_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / ".state.json"
            with patch("model_debate.STATE_PATH", state_path):
                models, mode = load_last_models()
            self.assertIsNone(models)
            self.assertIsNone(mode)

    def test_overwrite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / ".state.json"
            with patch("model_debate.STATE_PATH", state_path):
                save_last_models(["a"], "single")
                save_last_models(["b", "c"], "multi")
                models, mode = load_last_models()
            self.assertEqual(models, ["b", "c"])
            self.assertEqual(mode, "multi")


class TestInitConfig(unittest.TestCase):
    """Test config file generation."""

    def test_generates_both_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "model-debate.yaml"
            json_path = Path(tmpdir) / "model-debate.json"
            with patch("model_debate.CONFIG_PATH", yaml_path), \
                 patch("model_debate.CONFIG_JSON_PATH", json_path):
                init_config()

            self.assertTrue(yaml_path.exists())
            self.assertTrue(json_path.exists())

            config = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertIn("models", config)
            self.assertIn("gpt4o", config["models"])
            self.assertIn("claude-sonnet", config["models"])
            self.assertIn("gemini-flash", config["models"])
            self.assertEqual(config["debate"]["default_mode"], "single")
            self.assertEqual(config["debate"]["max_rounds"], 3)

    def test_yaml_content_matches_json(self):
        """YAML and JSON should contain equivalent data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "model-debate.yaml"
            json_path = Path(tmpdir) / "model-debate.json"
            with patch("model_debate.CONFIG_PATH", yaml_path), \
                 patch("model_debate.CONFIG_JSON_PATH", json_path):
                init_config()

            yaml_text = yaml_path.read_text(encoding="utf-8")
            # YAML should contain the model names
            self.assertIn("gpt4o:", yaml_text)
            self.assertIn("claude-sonnet:", yaml_text)
            self.assertIn("gemini-flash:", yaml_text)
            self.assertIn("participants: [gpt4o, claude-sonnet, gemini-flash]", yaml_text)


class TestSaveConfig(unittest.TestCase):
    """Test config save (JSON + YAML roundtrip)."""

    def test_save_and_reload_json(self):
        config = {
            "models": {
                "test-model": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "api_key_env": "TEST_KEY",
                    "endpoint": "https://api.openai.com/v1/chat/completions",
                    "max_tokens": 2048,
                }
            },
            "debate": {
                "participants": ["test-model"],
                "default_mode": "multi",
                "max_rounds": 5,
                "convergence_ratio": 0.9,
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "model-debate.yaml"
            json_path = Path(tmpdir) / "model-debate.json"
            with patch("model_debate.CONFIG_PATH", yaml_path), \
                 patch("model_debate.CONFIG_JSON_PATH", json_path):
                save_config(config)

            reloaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(reloaded["models"]["test-model"]["provider"], "openai")
            self.assertEqual(reloaded["debate"]["default_mode"], "multi")
            self.assertEqual(reloaded["debate"]["max_rounds"], 5)

    def test_yaml_output_contains_model_data(self):
        config = {
            "models": {
                "m1": {"provider": "anthropic", "model": "claude-sonnet-4-6"}
            },
            "debate": {"participants": ["m1"], "default_mode": "single", "max_rounds": 3, "convergence_ratio": 0.8},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "model-debate.yaml"
            json_path = Path(tmpdir) / "model-debate.json"
            with patch("model_debate.CONFIG_PATH", yaml_path), \
                 patch("model_debate.CONFIG_JSON_PATH", json_path):
                save_config(config)

            yaml_text = yaml_path.read_text(encoding="utf-8")
            self.assertIn("m1:", yaml_text)
            self.assertIn("provider: anthropic", yaml_text)
            self.assertIn("model: claude-sonnet-4-6", yaml_text)


class TestConstants(unittest.TestCase):
    """Test module-level constants are well-formed."""

    def test_retryable_status(self):
        self.assertIn(429, RETRYABLE_STATUS)
        self.assertIn(500, RETRYABLE_STATUS)
        self.assertIn(503, RETRYABLE_STATUS)
        self.assertNotIn(200, RETRYABLE_STATUS)
        self.assertNotIn(400, RETRYABLE_STATUS)

    def test_protocol_templates_keys(self):
        for key in ("openai", "anthropic", "google", "ollama"):
            self.assertIn(key, PROTOCOL_TEMPLATES)
            self.assertIn("default_endpoint", PROTOCOL_TEMPLATES[key])
            self.assertIn("default_key_env", PROTOCOL_TEMPLATES[key])

    def test_service_presets_keys(self):
        for key in ("openai", "anthropic", "google", "deepseek", "kimi", "groq", "ollama", "custom"):
            self.assertIn(key, SERVICE_PRESETS)
            self.assertIn("protocol", SERVICE_PRESETS[key])
            self.assertIn("endpoint", SERVICE_PRESETS[key])


if __name__ == "__main__":
    unittest.main()
