"""确定性时间解析核心，不依赖 Hermes 运行时。"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, tzinfo
from typing import Any, Optional
from zoneinfo import ZoneInfo


WEEKDAY_NAMES = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "日": 6,
    "天": 6,
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

CHINESE_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


@dataclass(frozen=True)
class TimezoneContext:
    tz: tzinfo
    name: str
    source: str
    trusted: bool


@dataclass(frozen=True)
class Resolution:
    status: str
    expression: str
    anchor_at: Optional[str]
    timezone: str
    timezone_source: str
    timezone_trusted: bool
    kind: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    certainty: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "expression": self.expression,
            "anchor_at": self.anchor_at,
            "timezone": self.timezone,
            "timezone_source": self.timezone_source,
            "timezone_trusted": self.timezone_trusted,
            "kind": self.kind,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "certainty": self.certainty,
            "reason": self.reason,
        }


def resolve_timezone(preferred: str = "") -> TimezoneContext:
    """按 Plugin 设置、Hermes 设置、系统时区的顺序解析时区。"""
    preferred = preferred.strip()
    if preferred:
        try:
            return TimezoneContext(ZoneInfo(preferred), preferred, "plugin", True)
        except (KeyError, ValueError):
            pass

    try:
        from hermes_time import get_timezone

        hermes_tz = get_timezone()
        if hermes_tz is not None:
            name = getattr(hermes_tz, "key", None) or str(hermes_tz)
            return TimezoneContext(hermes_tz, name, "hermes", True)
    except (ImportError, RuntimeError):
        pass

    local_tz = datetime.now().astimezone().tzinfo
    if local_tz is None:
        local_tz = ZoneInfo("UTC")
    name = getattr(local_tz, "key", None) or str(local_tz)
    return TimezoneContext(local_tz, name, "system", False)


def coerce_anchor(source_timestamp: Any, timezone_context: TimezoneContext) -> Optional[datetime]:
    if source_timestamp is None:
        return None
    try:
        if isinstance(source_timestamp, datetime):
            anchor = source_timestamp
            if anchor.tzinfo is None:
                anchor = anchor.replace(tzinfo=timezone_context.tz)
            return anchor.astimezone(timezone_context.tz)
        if isinstance(source_timestamp, str):
            anchor = datetime.fromisoformat(source_timestamp.replace("Z", "+00:00"))
            if anchor.tzinfo is None:
                anchor = anchor.replace(tzinfo=timezone_context.tz)
            return anchor.astimezone(timezone_context.tz)
        return datetime.fromtimestamp(float(source_timestamp), tz=timezone_context.tz)
    except (TypeError, ValueError, OverflowError):
        return None


def contains_temporal_signal(text: str) -> bool:
    normalized = text.lower()
    patterns = (
        r"今天|明天|后天|昨天|前天|周[一二三四五六日天末]|星期[一二三四五六日天]",
        r"上周|下周|本周|这周|本月|下个月|上个月|今年|明年|去年",
        r"\d+\s*(?:天|周|个月|月|年)(?:后|前)",
        r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}月\d{1,2}[日号]",
        r"\b(?:today|tomorrow|yesterday|next|last|this)\b",
        r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b(?:in\s+\d+\s+(?:days?|weeks?|months?|years?)|\d+\s+(?:days?|weeks?|months?|years?)\s+ago)\b",
    )
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns)


def resolve_expression(
    expression: str,
    source_timestamp: Any,
    timezone_name: str = "",
) -> Resolution:
    timezone_context = resolve_timezone(timezone_name)
    anchor = coerce_anchor(source_timestamp, timezone_context)
    raw_expression = (expression or "").strip()
    if anchor is None:
        return Resolution(
            status="unsupported",
            expression=raw_expression,
            anchor_at=None,
            timezone=timezone_context.name,
            timezone_source=timezone_context.source,
            timezone_trusted=timezone_context.trusted,
            reason="missing_source_timestamp",
        )
    if not raw_expression:
        return _unsupported(raw_expression, anchor, timezone_context, "empty_expression")

    normalized = _normalize_expression(raw_expression)
    return _resolve_normalized(normalized, raw_expression, anchor, timezone_context, allow_interval=True)


def expression_requires_source_timestamp(expression: str) -> bool:
    """判断支持的表达是否需要用消息日期补全语义。"""
    normalized = _normalize_expression(expression or "")
    interval = _split_interval(normalized)
    if interval is not None:
        return any(expression_requires_source_timestamp(part) for part in interval)
    date_text, _, _ = _extract_time(normalized, datetime(2000, 1, 1))
    return not bool(
        re.fullmatch(
            r"(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{4}年\d{1,2}月\d{1,2}[日号]?)",
            date_text.strip(),
        )
    )


def _resolve_normalized(
    normalized: str,
    raw_expression: str,
    anchor: datetime,
    timezone_context: TimezoneContext,
    *,
    allow_interval: bool,
) -> Resolution:
    if allow_interval:
        interval = _split_interval(normalized)
        if interval is not None:
            left, right = interval
            left_result = _resolve_normalized(
                left, left, anchor, timezone_context, allow_interval=False
            )
            right_result = _resolve_normalized(
                right, right, anchor, timezone_context, allow_interval=False
            )
            if left_result.status != "resolved" or right_result.status != "resolved":
                return _unsupported(raw_expression, anchor, timezone_context, "unsupported_interval_endpoint")
            start_at = left_result.start_at
            end_at = right_result.end_at or right_result.start_at
            if not start_at or not end_at or start_at > end_at:
                return _unsupported(raw_expression, anchor, timezone_context, "invalid_interval_order")
            certainty = (
                "inferred"
                if "inferred" in {left_result.certainty, right_result.certainty}
                else "deterministic"
            )
            return _resolved(
                raw_expression,
                anchor,
                timezone_context,
                "interval",
                start_at,
                end_at,
                certainty,
            )

    period = _resolve_period(normalized, anchor)
    if period is not None:
        start_dt, end_dt = period
        return _resolved(
            raw_expression,
            anchor,
            timezone_context,
            "interval",
            start_dt.isoformat(),
            end_dt.isoformat(),
            "deterministic",
        )

    text_without_time, parsed_time, time_certainty = _extract_time(normalized, anchor)
    date_result = _resolve_date(text_without_time, anchor)
    if date_result is None:
        if parsed_time is None:
            return _unsupported(raw_expression, anchor, timezone_context, "unsupported_expression")
        target_date = anchor.date()
        target_dt = datetime.combine(target_date, parsed_time, tzinfo=anchor.tzinfo)
        certainty = "deterministic"
        reason = None
        if target_dt < anchor:
            certainty = "inferred"
            reason = "time_only_already_passed"
        return _resolved(
            raw_expression,
            anchor,
            timezone_context,
            "datetime",
            target_dt.isoformat(),
            None,
            certainty,
            reason,
        )

    target_date, date_certainty, date_reason = date_result
    if parsed_time is not None:
        target_dt = datetime.combine(target_date, parsed_time, tzinfo=anchor.tzinfo)
        certainty = "inferred" if "inferred" in {date_certainty, time_certainty} else "deterministic"
        return _resolved(
            raw_expression,
            anchor,
            timezone_context,
            "datetime",
            target_dt.isoformat(),
            None,
            certainty,
            date_reason,
        )

    start_dt, end_dt = _day_bounds(target_date, anchor.tzinfo)
    return _resolved(
        raw_expression,
        anchor,
        timezone_context,
        "date",
        start_dt.isoformat(),
        end_dt.isoformat(),
        date_certainty,
        date_reason,
    )


def _normalize_expression(expression: str) -> str:
    text = expression.strip().lower()
    replacements = {
        "今晚": "今天晚上",
        "今早": "今天早上",
        "明晚": "明天晚上",
        "明早": "明天早上",
        "后天早": "后天早上",
        "day after tomorrow": "day_after_tomorrow",
        "two days ago": "two_days_ago",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text).strip(" ，,。.")


def _split_interval(expression: str) -> Optional[tuple[str, str]]:
    match = re.fullmatch(r"(?:从)?(.+?)(?:到|至)(.+)", expression)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    match = re.fullmatch(r"(.+?)\s+(?:to|through|until)\s+(.+)", expression)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None


def _resolve_period(expression: str, anchor: datetime) -> Optional[tuple[datetime, datetime]]:
    week_offsets = {
        "本周": 0,
        "这周": 0,
        "下周": 1,
        "下下周": 2,
        "上周": -1,
        "上上周": -2,
        "this week": 0,
        "next week": 1,
        "last week": -1,
    }
    if expression in week_offsets:
        monday = anchor.date() - timedelta(days=anchor.weekday())
        start_date = monday + timedelta(weeks=week_offsets[expression])
        end_date = start_date + timedelta(days=6)
        return _interval_bounds(start_date, end_date, anchor.tzinfo)

    weekend_offsets = {
        "本周末": 0,
        "这周末": 0,
        "下周末": 1,
        "上周末": -1,
        "this weekend": 0,
        "next weekend": 1,
        "last weekend": -1,
    }
    if expression in weekend_offsets:
        monday = anchor.date() - timedelta(days=anchor.weekday())
        saturday = monday + timedelta(weeks=weekend_offsets[expression], days=5)
        return _interval_bounds(saturday, saturday + timedelta(days=1), anchor.tzinfo)

    month_offsets = {
        "本月": 0,
        "这个月": 0,
        "下个月": 1,
        "上个月": -1,
        "this month": 0,
        "next month": 1,
        "last month": -1,
    }
    if expression in month_offsets:
        first = _shift_month(date(anchor.year, anchor.month, 1), month_offsets[expression])
        last = date(first.year, first.month, calendar.monthrange(first.year, first.month)[1])
        return _interval_bounds(first, last, anchor.tzinfo)

    year_offsets = {
        "今年": 0,
        "明年": 1,
        "去年": -1,
        "this year": 0,
        "next year": 1,
        "last year": -1,
    }
    if expression in year_offsets:
        year = anchor.year + year_offsets[expression]
        return _interval_bounds(date(year, 1, 1), date(year, 12, 31), anchor.tzinfo)
    return None


def _extract_time(expression: str, anchor: datetime) -> tuple[str, Optional[time], str]:
    zh_match = re.search(
        r"(凌晨|早上|上午|中午|下午|晚上)?\s*(\d{1,2})(?:[:：](\d{1,2})|点(半|\d{1,2}分?)?)",
        expression,
    )
    if zh_match:
        modifier, hour_text, minute_text, point_suffix = zh_match.groups()
        hour = int(hour_text)
        minute = int(minute_text) if minute_text else 0
        if point_suffix == "半":
            minute = 30
        elif point_suffix and point_suffix.endswith("分"):
            minute = int(point_suffix[:-1])
        hour = _apply_day_period(hour, modifier)
        if hour > 23 or minute > 59:
            return expression, None, "inferred"
        remaining = (expression[: zh_match.start()] + expression[zh_match.end() :]).strip()
        return remaining, time(hour, minute), "deterministic"

    en_match = re.search(
        r"(?:\bat\s+)?\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
        expression,
    )
    if en_match:
        hour = int(en_match.group(1))
        minute = int(en_match.group(2) or 0)
        hour = _apply_day_period(hour, en_match.group(3))
        if hour > 23 or minute > 59:
            return expression, None, "inferred"
        remaining = (expression[: en_match.start()] + expression[en_match.end() :]).strip()
        return remaining, time(hour, minute), "deterministic"

    at_match = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\b", expression)
    if at_match:
        hour = int(at_match.group(1))
        minute = int(at_match.group(2) or 0)
        if hour > 23 or minute > 59:
            return expression, None, "inferred"
        remaining = (expression[: at_match.start()] + expression[at_match.end() :]).strip()
        return remaining, time(hour, minute), "inferred"
    return expression, None, "deterministic"


def _apply_day_period(hour: int, modifier: Optional[str]) -> int:
    if modifier in {"下午", "晚上", "pm"} and hour < 12:
        return hour + 12
    if modifier == "中午" and hour < 11:
        return hour + 12
    if modifier in {"凌晨", "am"} and hour == 12:
        return 0
    return hour


def _resolve_date(expression: str, anchor: datetime) -> Optional[tuple[date, str, Optional[str]]]:
    text = expression.strip(" ，,。.")
    relative_days = {
        "今天": 0,
        "今日": 0,
        "明天": 1,
        "后天": 2,
        "昨天": -1,
        "前天": -2,
        "today": 0,
        "tomorrow": 1,
        "day_after_tomorrow": 2,
        "yesterday": -1,
        "two_days_ago": -2,
    }
    if text in relative_days:
        return anchor.date() + timedelta(days=relative_days[text]), "deterministic", None

    absolute = _parse_absolute_date(text, anchor.date())
    if absolute is not None:
        return absolute

    relative_duration = _parse_relative_duration(text, anchor.date())
    if relative_duration is not None:
        return relative_duration, "deterministic", None

    relative_month_day = re.fullmatch(r"(上个月|本月|这个月|下个月)\s*(\d{1,2})[日号]?", text)
    if relative_month_day:
        offsets = {"上个月": -1, "本月": 0, "这个月": 0, "下个月": 1}
        month_start = _shift_month(date(anchor.year, anchor.month, 1), offsets[relative_month_day.group(1)])
        day = int(relative_month_day.group(2))
        if day > calendar.monthrange(month_start.year, month_start.month)[1]:
            return None
        return date(month_start.year, month_start.month, day), "deterministic", None

    zh_weekday = re.fullmatch(r"(上上|上|本|这|下下|下)?(?:周|星期|礼拜)([一二三四五六日天])", text)
    if zh_weekday:
        prefix, weekday_name = zh_weekday.groups()
        return _resolve_weekday(prefix, WEEKDAY_NAMES[weekday_name], anchor.date())

    en_weekday = re.fullmatch(
        r"(?:(this|next|last)\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        text,
    )
    if en_weekday:
        prefix, weekday_name = en_weekday.groups()
        return _resolve_weekday(prefix, WEEKDAY_NAMES[weekday_name], anchor.date())
    return None


def _parse_absolute_date(text: str, anchor_date: date) -> Optional[tuple[date, str, Optional[str]]]:
    match = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if match:
        return _safe_date(*map(int, match.groups()), certainty="deterministic")

    match = re.fullmatch(r"(?:(\d{4})年)?(\d{1,2})月(\d{1,2})[日号]?", text)
    if match:
        year_text, month_text, day_text = match.groups()
        year = int(year_text) if year_text else anchor_date.year
        certainty = "deterministic"
        reason = None
        candidate = _safe_date(year, int(month_text), int(day_text), certainty=certainty)
        if candidate is None:
            return None
        target_date = candidate[0]
        if year_text is None and target_date < anchor_date:
            target_date = date(year + 1, target_date.month, target_date.day)
            certainty = "inferred"
            reason = "year_omitted_rolled_forward"
        return target_date, certainty, reason

    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})", text)
    if match:
        month, day = map(int, match.groups())
        candidate = _safe_date(anchor_date.year, month, day, certainty="deterministic")
        if candidate is None:
            return None
        target_date = candidate[0]
        if target_date < anchor_date:
            return date(anchor_date.year + 1, month, day), "inferred", "year_omitted_rolled_forward"
        return target_date, "deterministic", None
    return None


def _safe_date(year: int, month: int, day: int, *, certainty: str) -> Optional[tuple[date, str, Optional[str]]]:
    try:
        return date(year, month, day), certainty, None
    except ValueError:
        return None


def _parse_relative_duration(text: str, anchor_date: date) -> Optional[date]:
    zh_after = re.fullmatch(r"过([零一二两三四五六七八九十百\d]+)(天|周|个?月|年)", text)
    if zh_after:
        amount = _parse_number(zh_after.group(1))
        if amount is None:
            return None
        return _shift_duration(anchor_date, amount, zh_after.group(2))

    zh_match = re.fullmatch(r"(?:过)?([零一二两三四五六七八九十百\d]+)(天|周|个?月|年)(后|前)", text)
    if zh_match:
        amount = _parse_number(zh_match.group(1))
        if amount is None:
            return None
        direction = 1 if zh_match.group(3) == "后" else -1
        return _shift_duration(anchor_date, amount * direction, zh_match.group(2))

    en_future = re.fullmatch(r"in\s+(\d+)\s+(days?|weeks?|months?|years?)", text)
    if en_future:
        return _shift_duration(anchor_date, int(en_future.group(1)), en_future.group(2))
    en_past = re.fullmatch(r"(\d+)\s+(days?|weeks?|months?|years?)\s+ago", text)
    if en_past:
        return _shift_duration(anchor_date, -int(en_past.group(1)), en_past.group(2))
    return None


def _shift_duration(anchor_date: date, amount: int, unit: str) -> date:
    if unit in {"天", "day", "days"}:
        return anchor_date + timedelta(days=amount)
    if unit in {"周", "week", "weeks"}:
        return anchor_date + timedelta(weeks=amount)
    if unit in {"月", "个月", "month", "months"}:
        return _shift_month(anchor_date, amount)
    return _shift_year(anchor_date, amount)


def _parse_number(text: str) -> Optional[int]:
    if text.isdigit():
        return int(text)
    if text == "十":
        return 10
    if text == "百":
        return 100
    if "百" in text:
        hundreds, _, rest = text.partition("百")
        base = CHINESE_DIGITS.get(hundreds, 1) * 100
        return base + (_parse_number(rest) or 0)
    if "十" in text:
        tens, _, ones = text.partition("十")
        base = CHINESE_DIGITS.get(tens, 1) * 10
        return base + CHINESE_DIGITS.get(ones, 0)
    if len(text) == 1:
        return CHINESE_DIGITS.get(text)
    return None


def _resolve_weekday(prefix: Optional[str], weekday: int, anchor_date: date) -> tuple[date, str, Optional[str]]:
    prefix_offsets = {
        "上上": -2,
        "上": -1,
        "本": 0,
        "这": 0,
        "下": 1,
        "下下": 2,
        "last": -1,
        "this": 0,
        "next": 1,
    }
    if prefix in prefix_offsets:
        monday = anchor_date - timedelta(days=anchor_date.weekday())
        return monday + timedelta(weeks=prefix_offsets[prefix], days=weekday), "deterministic", None
    days_ahead = (weekday - anchor_date.weekday()) % 7
    return anchor_date + timedelta(days=days_ahead), "deterministic", None


def _shift_month(source: date, months: int) -> date:
    month_index = source.year * 12 + source.month - 1 + months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    day = min(source.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _shift_year(source: date, years: int) -> date:
    year = source.year + years
    day = min(source.day, calendar.monthrange(year, source.month)[1])
    return date(year, source.month, day)


def _day_bounds(target: date, zone: tzinfo) -> tuple[datetime, datetime]:
    return (
        datetime.combine(target, time.min, tzinfo=zone),
        datetime.combine(target, time.max, tzinfo=zone),
    )


def _interval_bounds(start_date: date, end_date: date, zone: tzinfo) -> tuple[datetime, datetime]:
    return _day_bounds(start_date, zone)[0], _day_bounds(end_date, zone)[1]


def _resolved(
    expression: str,
    anchor: datetime,
    timezone_context: TimezoneContext,
    kind: str,
    start_at: str,
    end_at: Optional[str],
    certainty: str,
    reason: Optional[str] = None,
) -> Resolution:
    return Resolution(
        status="resolved",
        expression=expression,
        anchor_at=anchor.isoformat(),
        timezone=timezone_context.name,
        timezone_source=timezone_context.source,
        timezone_trusted=timezone_context.trusted,
        kind=kind,
        start_at=start_at,
        end_at=end_at,
        certainty=certainty,
        reason=reason,
    )


def _unsupported(
    expression: str,
    anchor: datetime,
    timezone_context: TimezoneContext,
    reason: str,
) -> Resolution:
    return Resolution(
        status="unsupported",
        expression=expression,
        anchor_at=anchor.isoformat(),
        timezone=timezone_context.name,
        timezone_source=timezone_context.source,
        timezone_trusted=timezone_context.trusted,
        reason=reason,
    )
