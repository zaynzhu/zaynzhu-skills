from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from adapters.hermes.timeline_core import (
    contains_temporal_signal,
    expression_requires_source_timestamp,
    resolve_expression,
)


class TimelineCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.zone = ZoneInfo("Asia/Shanghai")
        self.friday = datetime(2026, 8, 28, 14, 0, tzinfo=self.zone)

    def resolve(self, expression: str, anchor: datetime | None = None):
        source = anchor or self.friday
        return resolve_expression(expression, source.timestamp(), "Asia/Shanghai")

    def test_tomorrow_uses_source_message_date(self) -> None:
        result = self.resolve("明天")
        self.assertEqual(result.status, "resolved")
        self.assertEqual(result.kind, "date")
        self.assertTrue(result.start_at.startswith("2026-08-29T00:00:00"))

    def test_next_weekday_uses_calendar_week(self) -> None:
        result = self.resolve("下周一")
        self.assertTrue(result.start_at.startswith("2026-08-31T00:00:00"))

    def test_next_week_is_closed_interval(self) -> None:
        result = self.resolve("下周")
        self.assertEqual(result.kind, "interval")
        self.assertTrue(result.start_at.startswith("2026-08-31T00:00:00"))
        self.assertTrue(result.end_at.startswith("2026-09-06T23:59:59.999999"))

    def test_relative_month_day(self) -> None:
        result = self.resolve("下个月3号")
        self.assertTrue(result.start_at.startswith("2026-09-03T00:00:00"))

    def test_month_shift_clamps_end_of_month(self) -> None:
        anchor = datetime(2026, 1, 31, 10, 0, tzinfo=self.zone)
        result = self.resolve("一个月后", anchor)
        self.assertTrue(result.start_at.startswith("2026-02-28T00:00:00"))

    def test_colloquial_after_duration(self) -> None:
        result = self.resolve("过两天")
        self.assertTrue(result.start_at.startswith("2026-08-30T00:00:00"))

    def test_time_point_keeps_relative_date(self) -> None:
        result = self.resolve("明天下午3点半")
        self.assertEqual(result.kind, "datetime")
        self.assertTrue(result.start_at.startswith("2026-08-29T15:30:00"))

    def test_interval_uses_inclusive_right_day(self) -> None:
        result = self.resolve("从明天到下周一")
        self.assertEqual(result.kind, "interval")
        self.assertTrue(result.start_at.startswith("2026-08-29T00:00:00"))
        self.assertTrue(result.end_at.startswith("2026-08-31T23:59:59.999999"))

    def test_cross_year_tomorrow(self) -> None:
        anchor = datetime(2026, 12, 31, 23, 0, tzinfo=self.zone)
        result = self.resolve("tomorrow", anchor)
        self.assertTrue(result.start_at.startswith("2027-01-01T00:00:00"))

    def test_time_only_after_clock_is_marked_inferred(self) -> None:
        anchor = datetime(2026, 8, 28, 21, 0, tzinfo=self.zone)
        result = self.resolve("晚上8点", anchor)
        self.assertEqual(result.certainty, "inferred")
        self.assertEqual(result.reason, "time_only_already_passed")

    def test_missing_timestamp_fails_closed(self) -> None:
        result = resolve_expression("明天", None, "Asia/Shanghai")
        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.reason, "missing_source_timestamp")

    def test_only_fully_qualified_dates_are_anchor_independent(self) -> None:
        self.assertFalse(expression_requires_source_timestamp("2026-09-01 下午3点"))
        self.assertFalse(
            expression_requires_source_timestamp("从2026-09-01到2026-09-03")
        )
        self.assertTrue(expression_requires_source_timestamp("明天下午3点"))
        self.assertTrue(expression_requires_source_timestamp("9月1日"))

    def test_signal_detection_covers_revision_language(self) -> None:
        self.assertTrue(contains_temporal_signal("那个改到下周五"))
        self.assertFalse(contains_temporal_signal("解释一下时间复杂度"))


if __name__ == "__main__":
    unittest.main()
