"""Tests for model_router.py — query classifier, candidate selection, request building.

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
SCRIPTS_DIR = Path(__file__).parent.parent / "skills" / "model-router" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from model_router import (
    classify_query,
    _profile_cost,
    select_candidates,
    build_request,
    extract_response,
    encode_image,
)


class TestClassifyQuery(unittest.TestCase):
    """Test the rule-based query classifier."""

    # --- has_image_input ---

    def test_has_image_flag_forces_image(self):
        task_type, confidence = classify_query("hello", has_image=True)
        self.assertEqual(task_type, "has_image_input")
        self.assertEqual(confidence, 1.0)

    def test_image_keyword_chinese(self):
        task_type, _ = classify_query("请识别一下这张图片中的文字")
        self.assertEqual(task_type, "has_image_input")

    def test_image_keyword_screenshot(self):
        task_type, _ = classify_query("看看这个 screenshot 有什么问题")
        self.assertEqual(task_type, "has_image_input")

    def test_image_keyword_captcha(self):
        task_type, _ = classify_query("帮我识别这个 captcha 验证码")
        self.assertEqual(task_type, "has_image_input")

    def test_image_keyword_ocr(self):
        task_type, _ = classify_query("ocr 这张图片")
        self.assertEqual(task_type, "has_image_input")

    def test_image_keyword_file_extension(self):
        task_type, _ = classify_query("看这个 png 文件")
        self.assertEqual(task_type, "has_image_input")

    # --- complex_reasoning ---

    def test_reasoning_keyword_analysis(self):
        task_type, _ = classify_query("请分析这段代码的架构设计")
        self.assertEqual(task_type, "complex_reasoning")

    def test_reasoning_keyword_review(self):
        task_type, _ = classify_query("帮我 review 一下这个 PR")
        self.assertEqual(task_type, "complex_reasoning")

    def test_reasoning_keyword_security(self):
        task_type, _ = classify_query("对这个系统进行安全审计")
        self.assertEqual(task_type, "complex_reasoning")

    def test_reasoning_long_query_with_keyword(self):
        # >30 words + reasoning keyword
        prompt = "请分析 " + " ".join(["word"] * 35) + " 架构"
        task_type, confidence = classify_query(prompt)
        self.assertEqual(task_type, "complex_reasoning")
        self.assertGreater(confidence, 0.5)

    def test_reasoning_very_long_query(self):
        # >100 words, no keyword needed
        prompt = " ".join(["word"] * 110)
        task_type, _ = classify_query(prompt)
        self.assertEqual(task_type, "complex_reasoning")

    # --- quick_task ---

    def test_quick_keyword_rename(self):
        task_type, _ = classify_query("重命名这个文件")
        self.assertEqual(task_type, "quick_task")

    def test_quick_keyword_format(self):
        task_type, _ = classify_query("格式化这段 JSON")
        self.assertEqual(task_type, "quick_task")

    def test_quick_keyword_translate(self):
        task_type, _ = classify_query("翻译这段话")
        self.assertEqual(task_type, "quick_task")

    def test_quick_short_query(self):
        # <20 words, no special keywords
        task_type, _ = classify_query("hello world")
        self.assertEqual(task_type, "quick_task")

    # --- general ---

    def test_general_medium_query(self):
        # 20-30 words, no special keywords
        prompt = " ".join(["word"] * 25)
        task_type, confidence = classify_query(prompt)
        self.assertEqual(task_type, "general")
        self.assertEqual(confidence, 0.5)

    def test_reasoning_keyword_overrides_short_query(self):
        # Has reasoning keyword but short — reasoning takes priority over quick_task
        task_type, _ = classify_query("分析这个")
        self.assertEqual(task_type, "complex_reasoning")

    def test_empty_string(self):
        task_type, confidence = classify_query("")
        self.assertEqual(task_type, "quick_task")


class TestProfileCost(unittest.TestCase):
    """Test cost calculation."""

    def test_with_cost(self):
        profile = {"cost": {"input_per_1m": 2.5, "output_per_1m": 10.0}}
        self.assertAlmostEqual(_profile_cost(profile), 12.5)

    def test_zero_cost(self):
        profile = {"cost": {"input_per_1m": 0, "output_per_1m": 0}}
        self.assertAlmostEqual(_profile_cost(profile), 0.0)

    def test_missing_cost(self):
        profile = {}
        self.assertAlmostEqual(_profile_cost(profile), 0)

    def test_partial_cost(self):
        profile = {"cost": {"input_per_1m": 5.0}}
        self.assertAlmostEqual(_profile_cost(profile), 5.0)


class TestSelectCandidates(unittest.TestCase):
    """Test candidate selection with cost sorting and API key filtering."""

    BASE_CONFIG = {
        "profiles": {
            "cheap": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key_env": "OPENAI_API_KEY",
                "cost": {"input_per_1m": 0.1, "output_per_1m": 0.4},
            },
            "expensive": {
                "provider": "anthropic",
                "model": "claude-opus-4-7",
                "api_key_env": "ANTHROPIC_API_KEY",
                "cost": {"input_per_1m": 15.0, "output_per_1m": 75.0},
            },
            "mid": {
                "provider": "google",
                "model": "gemini-2.0-flash",
                "api_key_env": "GOOGLE_API_KEY",
                "cost": {"input_per_1m": 0.1, "output_per_1m": 0.4},
            },
            "local": {
                "provider": "ollama",
                "model": "llava",
                "api_key_env": None,
                "cost": {"input_per_1m": 0, "output_per_1m": 0},
            },
        },
        "routing": [
            {"match": "quick_task", "prefer": ["cheap", "mid"], "cost_mode": "cheapest"},
            {"match": "complex_reasoning", "prefer": ["expensive"], "cost_mode": "best"},
            {"match": "has_image_input", "prefer": ["cheap", "mid", "local"], "cost_mode": "cheapest"},
        ],
    }

    def test_direct_profile(self):
        candidates = select_candidates(self.BASE_CONFIG, profile_name="cheap")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0][0], "cheap")

    def test_direct_profile_not_found(self):
        with self.assertRaises(KeyError):
            select_candidates(self.BASE_CONFIG, profile_name="nonexistent")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "GOOGLE_API_KEY": "test"})
    def test_cheapest_sorting(self):
        config = {
            "profiles": {
                "expensive": {
                    "provider": "openai", "model": "gpt-4o",
                    "api_key_env": "OPENAI_API_KEY",
                    "cost": {"input_per_1m": 15.0, "output_per_1m": 75.0},
                },
                "cheap": {
                    "provider": "google", "model": "gemini-2.0-flash",
                    "api_key_env": "GOOGLE_API_KEY",
                    "cost": {"input_per_1m": 0.1, "output_per_1m": 0.4},
                },
            },
            "routing": [
                {"match": "quick_task", "prefer": ["expensive", "cheap"], "cost_mode": "cheapest"},
            ],
        }
        candidates = select_candidates(config, task_type="quick_task")
        names = [c[0] for c in candidates]
        # cheapest sorts ascending — cheap should come before expensive
        self.assertEqual(names[0], "cheap")
        self.assertEqual(names[1], "expensive")

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"})
    def test_best_sorting(self):
        candidates = select_candidates(self.BASE_CONFIG, task_type="complex_reasoning")
        names = [c[0] for c in candidates]
        # best sorts descending by cost — expensive should be first
        self.assertEqual(names[0], "expensive")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    def test_missing_api_key_filters_out(self):
        """Profiles with unset API keys (except ollama) should be filtered."""
        candidates = select_candidates(self.BASE_CONFIG, task_type="quick_task")
        names = [c[0] for c in candidates]
        self.assertIn("cheap", names)
        # mid has GOOGLE_API_KEY unset — should NOT appear
        self.assertNotIn("mid", names)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "GOOGLE_API_KEY": "test"})
    def test_ollama_always_available(self):
        """Ollama (api_key_env=None) should always be available."""
        candidates = select_candidates(self.BASE_CONFIG, task_type="has_image_input")
        names = [c[0] for c in candidates]
        self.assertIn("local", names)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    def test_no_routing_match_uses_fallback(self):
        """When task_type matches no routing rule, all available profiles become candidates."""
        config = {
            "profiles": {
                "a": {"provider": "openai", "model": "m", "api_key_env": "OPENAI_API_KEY"},
                "b": {"provider": "ollama", "model": "m", "api_key_env": None},
            },
            "routing": [
                {"match": "has_image_input", "prefer": ["a"], "cost_mode": "cheapest"},
            ],
        }
        candidates = select_candidates(config, task_type="general")
        names = [c[0] for c in candidates]
        # No routing rule matches "general" — both profiles should appear via fallback
        self.assertIn("a", names)
        self.assertIn("b", names)


class TestBuildRequest(unittest.TestCase):
    """Test API request construction for all providers."""

    def test_openai(self):
        profile = {
            "provider": "openai",
            "model": "gpt-4o",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "api_key_env": "TEST_KEY",
            "max_tokens": 4096,
        }
        with patch.dict(os.environ, {"TEST_KEY": "sk-abc123"}):
            endpoint, headers, body = build_request(profile, "Hello")

        self.assertEqual(endpoint, "https://api.openai.com/v1/chat/completions")
        self.assertIn("Bearer sk-abc123", headers["Authorization"])
        body_json = json.loads(body)
        self.assertEqual(body_json["model"], "gpt-4o")
        self.assertEqual(body_json["messages"][0]["role"], "user")

    def test_anthropic(self):
        profile = {
            "provider": "anthropic",
            "model": "claude-sonnet-4-6",
            "endpoint": "https://api.anthropic.com/v1/messages",
            "api_key_env": "TEST_KEY",
            "max_tokens": 4096,
        }
        with patch.dict(os.environ, {"TEST_KEY": "sk-ant-abc"}):
            endpoint, headers, body = build_request(profile, "Hello")

        self.assertEqual(headers["x-api-key"], "sk-ant-abc")
        self.assertEqual(headers["anthropic-version"], "2023-06-01")
        body_json = json.loads(body)
        self.assertEqual(body_json["model"], "claude-sonnet-4-6")

    def test_google(self):
        profile = {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "api_key_env": "TEST_KEY",
            "max_tokens": 4096,
        }
        with patch.dict(os.environ, {"TEST_KEY": "google-key-123"}):
            endpoint, headers, body = build_request(profile, "Hello")

        self.assertIn("key=google-key-123", endpoint)
        body_json = json.loads(body)
        self.assertIn("contents", body_json)

    def test_ollama(self):
        profile = {
            "provider": "ollama",
            "model": "llava",
            "endpoint": "http://localhost:11434/api/generate",
            "api_key_env": None,
            "max_tokens": 4096,
        }
        endpoint, headers, body = build_request(profile, "Hello")
        self.assertEqual(endpoint, "http://localhost:11434/api/generate")
        body_json = json.loads(body)
        self.assertEqual(body_json["model"], "llava")
        self.assertEqual(body_json["prompt"], "Hello")
        self.assertFalse(body_json["stream"])

    def test_generic_provider(self):
        profile = {
            "provider": "custom",
            "model": "my-model",
            "endpoint": "https://custom.api.com/v1/chat",
            "api_key_env": "CUSTOM_KEY",
            "max_tokens": 2048,
        }
        with patch.dict(os.environ, {"CUSTOM_KEY": "custom-secret"}):
            endpoint, headers, body = build_request(profile, "Hello")

        self.assertIn("Bearer custom-secret", headers["Authorization"])


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
        """choices=[None] should return '', not crash."""
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

    def test_unknown_provider(self):
        resp = {"result": "some data"}
        result = extract_response("unknown", resp)
        # Should return JSON string
        self.assertIn("some data", result)


class TestEncodeImage(unittest.TestCase):
    """Test image base64 encoding."""

    def test_encode_png(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            f.flush()
            path = f.name
        try:
            mime, data = encode_image(path)
            self.assertEqual(mime, "image/png")
            self.assertTrue(len(data) > 0)
        finally:
            os.unlink(path)

    def test_encode_jpg(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff" + b"\x00" * 100)
            f.flush()
            path = f.name
        try:
            mime, data = encode_image(path)
            self.assertEqual(mime, "image/jpeg")
        finally:
            os.unlink(path)

    def test_encode_unknown_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"\x00" * 10)
            f.flush()
            path = f.name
        try:
            mime, _ = encode_image(path)
            self.assertEqual(mime, "image/png")  # default
        finally:
            os.unlink(path)

    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            encode_image("/nonexistent/path/image.png")


if __name__ == "__main__":
    unittest.main()
