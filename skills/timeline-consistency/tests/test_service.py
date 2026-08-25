from __future__ import annotations

import json
import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from adapters.hermes.service import TimelineService
from adapters.hermes.storage import TimelineStore


class TimelineServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        connection = sqlite3.connect(":memory:", check_same_thread=False)
        connection.execute("PRAGMA foreign_keys=ON")
        self.connection = connection
        self.service = TimelineService(
            TimelineStore(connection),
            "Asia/Shanghai",
            trust_remote_timestamps=True,
        )
        self.friday = datetime(2026, 8, 28, 14, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    def start_turn(self, session_id: str, text: str, timestamp: datetime | None = None):
        row = {"role": "user", "content": text}
        if timestamp is not None:
            row["timestamp"] = timestamp.timestamp()
        return self.service.pre_llm_call(
            session_id=session_id,
            user_message=text,
            conversation_history=[row],
            platform="telegram",
            sender_id="user-1",
        )

    def test_hook_injects_source_timestamp_without_mutating_history(self) -> None:
        history = [{"role": "user", "content": "我明天请假", "timestamp": self.friday.timestamp()}]
        result = self.service.pre_llm_call(
            session_id="s1",
            user_message="我明天请假",
            conversation_history=history,
            platform="telegram",
            sender_id="user-1",
        )
        self.assertIn("2026-08-28T14:00:00+08:00", result["context"])
        self.assertIn("source_timestamp_trusted: true", result["context"])
        self.assertEqual(history[0]["content"], "我明天请假")

    def test_one_off_temporal_query_does_not_inject_or_create_context(self) -> None:
        result = self.start_turn("s-weather", "明天上海天气如何？", self.friday)
        self.assertIsNone(result)

    def test_existing_event_does_not_make_weather_query_inject(self) -> None:
        self.start_turn("s-weather-event", "我明天看电影", self.friday)
        self.service.handle_resolve(
            {"label": "看电影", "expression": "明天", "risk_level": "low"},
            session_id="s-weather-event",
        )
        result = self.start_turn(
            "s-weather-event",
            "明天天气如何？",
            self.friday,
        )
        self.assertIsNone(result)

    def test_information_keywords_do_not_hide_real_timeline_facts(self) -> None:
        booking = self.start_turn(
            "s-weather-exhibition",
            "我明天预约看天气展",
            self.friday,
        )
        translation = self.start_turn(
            "s-translation-deadline",
            "我需要明天前翻译完合同",
            self.friday,
        )
        translation_plan = self.start_turn(
            "s-translation-plan",
            "我明天要翻译合同",
            self.friday,
        )
        self.assertIsNotNone(booking)
        self.assertIsNotNone(translation)
        self.assertIsNotNone(translation_plan)

    def test_action_request_without_time_does_not_inject_context(self) -> None:
        result = self.start_turn("s-booking", "帮我预约一家餐厅", self.friday)
        self.assertIsNone(result)

    def test_resolve_commits_before_answer(self) -> None:
        self.start_turn("s1", "我明天请假", self.friday)
        result = json.loads(
            self.service.handle_resolve(
                {
                    "label": "请假",
                    "expression": "明天",
                    "risk_level": "high",
                    "status": "planned",
                },
                session_id="s1",
            )
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["needs_confirmation"])
        self.assertTrue(result["event"]["start_at"].startswith("2026-08-29"))

    def test_obvious_high_risk_cannot_be_downgraded_by_model(self) -> None:
        self.start_turn("s-risk", "我明天吃药", self.friday)
        result = json.loads(
            self.service.handle_resolve(
                {
                    "label": "吃药",
                    "expression": "明天",
                    "risk_level": "low",
                },
                session_id="s-risk",
            )
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["event"]["risk_level"], "high")

    def test_gateway_owner_key_does_not_store_raw_sender_id(self) -> None:
        self.start_turn("s-owner", "我明天看电影", self.friday)
        self.service.handle_resolve(
            {"label": "看电影", "expression": "明天", "risk_level": "low"},
            session_id="s-owner",
        )
        owner_key = self.connection.execute(
            "SELECT owner_key FROM timeline_events LIMIT 1"
        ).fetchone()[0]
        self.assertTrue(owner_key.startswith("telegram:sha256:"))
        self.assertNotIn("user-1", owner_key)

    def test_cross_session_query_keeps_original_absolute_date(self) -> None:
        self.start_turn("s1", "我明天请假", self.friday)
        created = json.loads(
            self.service.handle_resolve(
                {"label": "请假", "expression": "明天", "risk_level": "high"},
                session_id="s1",
            )
        )
        monday = datetime(2026, 8, 31, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        self.start_turn("s2", "我之前说的请假是哪天？", monday)
        queried = json.loads(self.service.handle_query({"query": "请假"}, session_id="s2"))
        self.assertEqual(queried["events"][0]["id"], created["event"]["id"])
        self.assertTrue(queried["events"][0]["start_at"].startswith("2026-08-29"))

    def test_high_risk_inferred_time_requires_confirmation(self) -> None:
        late = datetime(2026, 8, 28, 21, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        self.start_turn("s1", "晚上8点吃药", late)
        result = json.loads(
            self.service.handle_resolve(
                {"label": "吃药", "expression": "晚上8点", "risk_level": "high"},
                session_id="s1",
            )
        )
        self.assertTrue(result["needs_confirmation"])
        self.assertEqual(result["reason"], "time_only_already_passed")

    def test_remote_timestamp_requires_opt_in_for_high_risk_event(self) -> None:
        connection = sqlite3.connect(":memory:", check_same_thread=False)
        connection.execute("PRAGMA foreign_keys=ON")
        service = TimelineService(TimelineStore(connection), "Asia/Shanghai")
        service.pre_llm_call(
            session_id="s-remote",
            user_message="我明天请假",
            conversation_history=[
                {
                    "role": "user",
                    "content": "我明天请假",
                    "timestamp": self.friday.timestamp(),
                }
            ],
            platform="telegram",
            sender_id="user-1",
        )
        result = json.loads(
            service.handle_resolve(
                {"label": "请假", "expression": "明天", "risk_level": "high"},
                session_id="s-remote",
            )
        )
        self.assertTrue(result["needs_confirmation"])
        self.assertEqual(result["reason"], "source_timestamp_untrusted")

    def test_absolute_date_does_not_depend_on_remote_timestamp_trust(self) -> None:
        connection = sqlite3.connect(":memory:", check_same_thread=False)
        connection.execute("PRAGMA foreign_keys=ON")
        service = TimelineService(TimelineStore(connection), "Asia/Shanghai")
        service.pre_llm_call(
            session_id="s-absolute",
            user_message="我在2026-09-01请假",
            conversation_history=[
                {
                    "role": "user",
                    "content": "我在2026-09-01请假",
                    "timestamp": self.friday.timestamp(),
                }
            ],
            platform="telegram",
            sender_id="user-1",
        )
        result = json.loads(
            service.handle_resolve(
                {
                    "label": "请假",
                    "expression": "2026-09-01",
                    "risk_level": "high",
                },
                session_id="s-absolute",
            )
        )
        self.assertFalse(result["needs_confirmation"])
        self.assertEqual(result["event"]["certainty"], "deterministic")

    def test_revision_cannot_downgrade_existing_high_risk_event(self) -> None:
        connection = sqlite3.connect(":memory:", check_same_thread=False)
        connection.execute("PRAGMA foreign_keys=ON")
        service = TimelineService(TimelineStore(connection), "Asia/Shanghai")
        source = {
            "role": "user",
            "content": "我在2026-09-01请假",
            "timestamp": self.friday.timestamp(),
        }
        service.pre_llm_call(
            session_id="s-risk-revision",
            user_message=source["content"],
            conversation_history=[source],
            platform="telegram",
            sender_id="user-1",
        )
        created = json.loads(
            service.handle_resolve(
                {
                    "label": "请假",
                    "expression": "2026-09-01",
                    "risk_level": "high",
                },
                session_id="s-risk-revision",
            )
        )
        revision_text = "改到明天"
        service.pre_llm_call(
            session_id="s-risk-revision",
            user_message=revision_text,
            conversation_history=[
                {
                    "role": "user",
                    "content": revision_text,
                    "timestamp": self.friday.timestamp(),
                }
            ],
            platform="telegram",
            sender_id="user-1",
        )
        pending = json.loads(
            service.handle_revise(
                {
                    "event_id": created["event"]["id"],
                    "expression": "明天",
                    "risk_level": "low",
                },
                session_id="s-risk-revision",
            )
        )
        self.assertTrue(pending["needs_confirmation"])
        self.assertEqual(pending["reason"], "source_timestamp_untrusted")
        confirmed = json.loads(
            service.handle_revise(
                {
                    "confirmation_token": pending["confirmation_token"],
                    "confirmed": True,
                },
                session_id="s-risk-revision",
            )
        )
        self.assertEqual(confirmed["event"]["risk_level"], "high")

    def test_confirmation_token_commits_once(self) -> None:
        late = datetime(2026, 8, 28, 21, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        self.start_turn("s1", "晚上8点吃药", late)
        pending = json.loads(
            self.service.handle_resolve(
                {"label": "吃药", "expression": "晚上8点", "risk_level": "high"},
                session_id="s1",
            )
        )
        committed = json.loads(
            self.service.handle_resolve(
                {"confirmation_token": pending["confirmation_token"], "confirmed": True},
                session_id="s1",
            )
        )
        self.assertTrue(committed["ok"])
        self.assertEqual(committed["event"]["certainty"], "confirmed")

    def test_revision_inherits_high_risk_confirmation_rule(self) -> None:
        self.start_turn("s1", "我明天请假", self.friday)
        created = json.loads(
            self.service.handle_resolve(
                {"label": "请假", "expression": "明天", "risk_level": "high"},
                session_id="s1",
            )
        )
        late = datetime(2026, 8, 31, 21, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        self.start_turn("s1", "改到晚上8点", late)
        revised = json.loads(
            self.service.handle_revise(
                {"event_id": created["event"]["id"], "expression": "晚上8点"},
                session_id="s1",
            )
        )
        self.assertTrue(revised["needs_confirmation"])
        self.assertEqual(revised["reason"], "time_only_already_passed")

    def test_missing_timestamp_fails_closed(self) -> None:
        injected = self.start_turn("s1", "我明天请假", None)
        self.assertIn("mode: degraded", injected["context"])
        self.assertNotIn("mode: full", injected["context"])
        self.assertNotIn("Create or revise temporal facts", injected["context"])
        result = json.loads(
            self.service.handle_resolve(
                {"label": "请假", "expression": "明天", "risk_level": "high"},
                session_id="s1",
            )
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "missing_source_timestamp")

    def test_stale_history_timestamp_is_not_used_for_current_message(self) -> None:
        result = self.service.pre_llm_call(
            session_id="s-stale",
            user_message="我明天请假",
            conversation_history=[
                {
                    "role": "user",
                    "content": "上一条消息",
                    "timestamp": self.friday.timestamp(),
                }
            ],
            platform="telegram",
            sender_id="user-1",
        )
        self.assertIn("mode: degraded", result["context"])
        self.assertIn("source_timestamp: missing", result["context"])

    def test_query_still_works_when_current_turn_lacks_timestamp(self) -> None:
        self.start_turn("s1", "我明天请假", self.friday)
        self.service.handle_resolve(
            {"label": "请假", "expression": "明天", "risk_level": "high"},
            session_id="s1",
        )
        self.start_turn("s1", "我之前的请假是哪天？", None)
        result = json.loads(self.service.handle_query({"query": "请假"}, session_id="s1"))
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)

    def test_forget_requires_explicit_intent(self) -> None:
        self.start_turn("s1", "我明天请假", self.friday)
        created = json.loads(
            self.service.handle_resolve(
                {"label": "请假", "expression": "明天", "risk_level": "high"},
                session_id="s1",
            )
        )
        denied = json.loads(
            self.service.handle_forget(
                {"event_id": created["event"]["id"], "user_confirmed_forget": False},
                session_id="s1",
            )
        )
        self.assertEqual(denied["code"], "forget_not_confirmed")


if __name__ == "__main__":
    unittest.main()
