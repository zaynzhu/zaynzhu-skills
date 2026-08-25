from __future__ import annotations

import sqlite3
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from adapters.hermes.storage import SourceContext, TimelineStore
from adapters.hermes.timeline_core import resolve_expression


class TimelineStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        connection = sqlite3.connect(":memory:", check_same_thread=False)
        connection.execute("PRAGMA foreign_keys=ON")
        self.store = TimelineStore(connection)
        self.anchor = datetime(2026, 8, 28, 14, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        self.source = SourceContext(
            owner_key="telegram:user-1",
            session_id="s1",
            source_timestamp=self.anchor.timestamp(),
            source_ref="sha256:test",
        )

    def create_leave(self):
        resolution = resolve_expression("明天", self.anchor.timestamp(), "Asia/Shanghai")
        return self.store.create_event(
            source=self.source,
            label="请假",
            resolution=resolution,
            risk_level="high",
        )

    def test_create_and_query_are_owner_scoped(self) -> None:
        event = self.create_leave()
        self.assertEqual(event["version"], 1)
        self.assertEqual(len(self.store.query_events("telegram:user-1")), 1)
        self.assertEqual(self.store.query_events("telegram:user-2"), [])

    def test_create_retry_is_idempotent(self) -> None:
        first = self.create_leave()
        second = self.create_leave()
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(self.store.query_events("telegram:user-1", include_history=True)), 1)

    def test_revision_preserves_old_version(self) -> None:
        event = self.create_leave()
        monday = resolve_expression("下周一", self.anchor.timestamp(), "Asia/Shanghai")
        revised = self.store.revise_event(
            source=self.source,
            event_id=event["id"],
            resolution=monday,
        )
        self.assertEqual(revised["version"], 2)
        self.assertEqual(revised["supersedes_id"], event["id"])
        self.assertEqual(len(self.store.query_events("telegram:user-1")), 1)
        history = self.store.query_events("telegram:user-1", include_history=True)
        self.assertEqual(len(history), 2)
        self.assertFalse(next(item for item in history if item["id"] == event["id"])["is_current"])

    def test_status_change_creates_version(self) -> None:
        event = self.create_leave()
        completed = self.store.revise_event(
            source=self.source,
            event_id=event["id"],
            status="completed",
        )
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["version"], 2)

    def test_revision_retry_is_idempotent(self) -> None:
        event = self.create_leave()
        first = self.store.revise_event(source=self.source, event_id=event["id"], status="completed")
        second = self.store.revise_event(source=self.source, event_id=event["id"], status="completed")
        self.assertEqual(first["id"], second["id"])

    def test_forget_deletes_entire_version_chain(self) -> None:
        event = self.create_leave()
        token = self.store.create_pending(
            "telegram:user-1",
            "revise",
            {"event_id": event["id"]},
        )
        revised = self.store.revise_event(
            source=self.source,
            event_id=event["id"],
            status="cancelled",
        )
        deleted = self.store.forget_event("telegram:user-1", revised["id"])
        self.assertEqual(deleted, 2)
        self.assertEqual(self.store.query_events("telegram:user-1", include_history=True), [])
        with self.assertRaises(LookupError):
            self.store.consume_pending("telegram:user-1", token)

    def test_pending_confirmation_is_single_use(self) -> None:
        token = self.store.create_pending("telegram:user-1", "create", {"label": "请假"})
        action, payload = self.store.consume_pending("telegram:user-1", token)
        self.assertEqual(action, "create")
        self.assertEqual(payload["label"], "请假")
        with self.assertRaises(LookupError):
            self.store.consume_pending("telegram:user-1", token)

    def test_pending_action_mismatch_does_not_consume_token(self) -> None:
        token = self.store.create_pending("telegram:user-1", "create", {"label": "请假"})
        with self.assertRaises(LookupError):
            self.store.consume_pending(
                "telegram:user-1",
                token,
                expected_action="revise",
            )
        action, _ = self.store.consume_pending(
            "telegram:user-1",
            token,
            expected_action="create",
        )
        self.assertEqual(action, "create")

    def test_retention_prunes_only_terminal_roots(self) -> None:
        planned = self.create_leave()
        other_source = SourceContext(
            owner_key="telegram:user-1",
            session_id="s2",
            source_timestamp=self.anchor.timestamp() + 1,
            source_ref="sha256:terminal",
        )
        terminal = self.store.create_event(
            source=other_source,
            label="旧预约",
            resolution=resolve_expression("昨天", self.anchor.timestamp(), "Asia/Shanghai"),
            risk_level="low",
            status="historical",
        )
        deleted = self.store.prune_terminal_before("telegram:user-1", time.time() + 1)
        self.assertEqual(deleted, 1)
        remaining = self.store.query_events("telegram:user-1")
        self.assertEqual([event["id"] for event in remaining], [planned["id"]])
        with self.assertRaises(LookupError):
            self.store.get_event("telegram:user-1", terminal["id"])

    def test_close_releases_the_connection(self) -> None:
        connection = self.store._connection
        self.store.close()
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()
