"""Timeline Consistency 的独立 SQLite 账本。"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from .timeline_core import Resolution


ALLOWED_STATUSES = {"planned", "completed", "cancelled", "historical"}
ALLOWED_RISKS = {"low", "high"}


@dataclass(frozen=True)
class SourceContext:
    owner_key: str
    session_id: str
    source_timestamp: float
    source_ref: str


class TimelineStore:
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._initialize()

    def _initialize(self) -> None:
        with self._lock, self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS timeline_events (
                    id TEXT PRIMARY KEY,
                    root_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    supersedes_id TEXT,
                    owner_key TEXT NOT NULL,
                    label TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    start_at TEXT NOT NULL,
                    end_at TEXT,
                    timezone TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    certainty TEXT NOT NULL,
                    source_expression TEXT NOT NULL,
                    source_timestamp REAL NOT NULL,
                    source_session_id TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    is_current INTEGER NOT NULL DEFAULT 1,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (supersedes_id) REFERENCES timeline_events(id),
                    UNIQUE(root_id, version)
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_timeline_current_root
                    ON timeline_events(root_id) WHERE is_current = 1;

                CREATE INDEX IF NOT EXISTS idx_timeline_owner_current
                    ON timeline_events(owner_key, is_current, source_timestamp DESC);

                CREATE TABLE IF NOT EXISTS timeline_pending (
                    token TEXT PRIMARY KEY,
                    owner_key TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_timeline_pending_owner
                    ON timeline_pending(owner_key, expires_at);
                """
            )

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def create_event(
        self,
        *,
        source: SourceContext,
        label: str,
        resolution: Resolution,
        risk_level: str,
        status: str = "planned",
        certainty: Optional[str] = None,
    ) -> dict[str, Any]:
        _validate_event_input(label, resolution, risk_level, status)
        event_id = uuid.uuid4().hex
        created_at = time.time()
        with self._lock, self._connection:
            existing = self._connection.execute(
                """
                SELECT current.*
                FROM timeline_events AS initial
                JOIN timeline_events AS current
                  ON current.root_id = initial.root_id AND current.is_current = 1
                WHERE initial.owner_key = ?
                  AND initial.version = 1
                  AND initial.source_ref = ?
                  AND initial.label = ?
                  AND initial.source_expression = ?
                LIMIT 1
                """,
                (
                    source.owner_key,
                    source.source_ref,
                    label.strip(),
                    resolution.expression,
                ),
            ).fetchone()
            if existing is not None:
                return _row_to_event(existing)
            self._connection.execute(
                """
                INSERT INTO timeline_events (
                    id, root_id, version, supersedes_id, owner_key, label,
                    kind, start_at, end_at, timezone, status, risk_level,
                    certainty, source_expression, source_timestamp,
                    source_session_id, source_ref, is_current, created_at
                ) VALUES (?, ?, 1, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    event_id,
                    event_id,
                    source.owner_key,
                    label.strip(),
                    resolution.kind,
                    resolution.start_at,
                    resolution.end_at,
                    resolution.timezone,
                    status,
                    risk_level,
                    certainty or resolution.certainty or "deterministic",
                    resolution.expression,
                    source.source_timestamp,
                    source.session_id,
                    source.source_ref,
                    created_at,
                ),
            )
        return self.get_event(source.owner_key, event_id)

    def get_event(self, owner_key: str, event_id: str) -> dict[str, Any]:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM timeline_events WHERE owner_key = ? AND id = ?",
                (owner_key, event_id),
            ).fetchone()
        if row is None:
            raise LookupError("event_not_found")
        return _row_to_event(row)

    def query_events(
        self,
        owner_key: str,
        *,
        query: str = "",
        include_history: bool = False,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        current_clause = "" if include_history else "AND is_current = 1"
        with self._lock:
            rows = self._connection.execute(
                f"""
                SELECT * FROM timeline_events
                WHERE owner_key = ? {current_clause}
                ORDER BY is_current DESC, source_timestamp DESC, version DESC
                LIMIT 100
                """,
                (owner_key,),
            ).fetchall()
        events = [_row_to_event(row) for row in rows]
        if query.strip():
            events = _rank_events(events, query)
        return events[:limit]

    def relevant_events(self, owner_key: str, user_message: str, limit: int = 5) -> list[dict[str, Any]]:
        events = self.query_events(owner_key, limit=50)
        ranked = _rank_events(events, user_message)
        if ranked:
            return ranked[:limit]
        if re.search(r"那个|这件事|之前|最近|安排|计划|when|schedule|that|it", user_message, re.IGNORECASE):
            return events[: min(limit, 3)]
        return []

    def revise_event(
        self,
        *,
        source: SourceContext,
        event_id: str,
        resolution: Optional[Resolution] = None,
        label: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        certainty: Optional[str] = None,
        source_expression: Optional[str] = None,
    ) -> dict[str, Any]:
        if status is not None and status not in ALLOWED_STATUSES:
            raise ValueError("invalid_status")
        if risk_level is not None and risk_level not in ALLOWED_RISKS:
            raise ValueError("invalid_risk_level")
        if resolution is not None and resolution.status != "resolved":
            raise ValueError("resolution_not_resolved")

        created_at = time.time()
        new_id = uuid.uuid4().hex
        with self._lock, self._connection:
            existing = self._connection.execute(
                """
                SELECT * FROM timeline_events
                WHERE owner_key = ? AND supersedes_id = ?
                  AND source_ref = ? AND is_current = 1
                LIMIT 1
                """,
                (source.owner_key, event_id, source.source_ref),
            ).fetchone()
            if existing is not None:
                return _row_to_event(existing)
            current = self._connection.execute(
                """
                SELECT * FROM timeline_events
                WHERE owner_key = ? AND id = ? AND is_current = 1
                """,
                (source.owner_key, event_id),
            ).fetchone()
            if current is None:
                raise LookupError("current_event_not_found")

            self._connection.execute(
                "UPDATE timeline_events SET is_current = 0 WHERE id = ?",
                (event_id,),
            )
            self._connection.execute(
                """
                INSERT INTO timeline_events (
                    id, root_id, version, supersedes_id, owner_key, label,
                    kind, start_at, end_at, timezone, status, risk_level,
                    certainty, source_expression, source_timestamp,
                    source_session_id, source_ref, is_current, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    new_id,
                    current["root_id"],
                    current["version"] + 1,
                    current["id"],
                    source.owner_key,
                    (label or current["label"]).strip(),
                    resolution.kind if resolution else current["kind"],
                    resolution.start_at if resolution else current["start_at"],
                    resolution.end_at if resolution else current["end_at"],
                    resolution.timezone if resolution else current["timezone"],
                    status or current["status"],
                    risk_level or current["risk_level"],
                    certainty
                    or (resolution.certainty if resolution else None)
                    or current["certainty"],
                    source_expression
                    or (resolution.expression if resolution else None)
                    or current["source_expression"],
                    source.source_timestamp,
                    source.session_id,
                    source.source_ref,
                    created_at,
                ),
            )
        return self.get_event(source.owner_key, new_id)

    def forget_event(self, owner_key: str, event_id: str) -> int:
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT root_id FROM timeline_events WHERE owner_key = ? AND id = ?",
                (owner_key, event_id),
            ).fetchone()
            if row is None:
                raise LookupError("event_not_found")
            version_rows = self._connection.execute(
                "SELECT id FROM timeline_events WHERE owner_key = ? AND root_id = ?",
                (owner_key, row["root_id"]),
            ).fetchall()
            version_ids = {version["id"] for version in version_rows}
            pending_rows = self._connection.execute(
                "SELECT token, payload_json FROM timeline_pending WHERE owner_key = ?",
                (owner_key,),
            ).fetchall()
            pending_tokens = []
            for pending in pending_rows:
                try:
                    payload = json.loads(pending["payload_json"])
                except (TypeError, ValueError):
                    continue
                if payload.get("event_id") in version_ids:
                    pending_tokens.append(pending["token"])
            if pending_tokens:
                placeholders = ",".join("?" for _ in pending_tokens)
                self._connection.execute(
                    f"DELETE FROM timeline_pending WHERE owner_key = ? AND token IN ({placeholders})",
                    (owner_key, *pending_tokens),
                )
            cursor = self._connection.execute(
                "DELETE FROM timeline_events WHERE owner_key = ? AND root_id = ?",
                (owner_key, row["root_id"]),
            )
        return cursor.rowcount

    def create_pending(
        self,
        owner_key: str,
        action: str,
        payload: dict[str, Any],
        *,
        ttl_seconds: int = 900,
    ) -> str:
        token = uuid.uuid4().hex
        created_at = time.time()
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO timeline_pending (
                    token, owner_key, action, payload_json, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    token,
                    owner_key,
                    action,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    created_at,
                    created_at + ttl_seconds,
                ),
            )
        return token

    def consume_pending(
        self,
        owner_key: str,
        token: str,
        *,
        expected_action: Optional[str] = None,
    ) -> tuple[str, dict[str, Any]]:
        now = time.time()
        action_clause = "" if expected_action is None else "AND action = ?"
        parameters: tuple[Any, ...] = (owner_key, token, now)
        if expected_action is not None:
            parameters += (expected_action,)
        with self._lock, self._connection:
            row = self._connection.execute(
                f"""
                SELECT action, payload_json FROM timeline_pending
                WHERE owner_key = ? AND token = ? AND expires_at >= ?
                {action_clause}
                """,
                parameters,
            ).fetchone()
            if row is None:
                raise LookupError("confirmation_token_not_found")
            self._connection.execute(
                "DELETE FROM timeline_pending WHERE token = ?",
                (token,),
            )
        return row["action"], json.loads(row["payload_json"])

    def prune_expired_pending(self) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "DELETE FROM timeline_pending WHERE expires_at < ?",
                (time.time(),),
            )
        return cursor.rowcount

    def prune_terminal_before(self, owner_key: str, cutoff: float) -> int:
        with self._lock, self._connection:
            roots = self._connection.execute(
                """
                SELECT root_id FROM timeline_events
                WHERE owner_key = ? AND is_current = 1
                  AND status IN ('completed', 'cancelled', 'historical')
                  AND created_at < ?
                """,
                (owner_key, cutoff),
            ).fetchall()
            root_ids = [row["root_id"] for row in roots]
            if not root_ids:
                return 0
            placeholders = ",".join("?" for _ in root_ids)
            cursor = self._connection.execute(
                f"DELETE FROM timeline_events WHERE owner_key = ? AND root_id IN ({placeholders})",
                (owner_key, *root_ids),
            )
        return cursor.rowcount


def make_source_ref(session_id: str, source_timestamp: float, user_message: str) -> str:
    payload = f"{session_id}\0{source_timestamp:.6f}\0{user_message}".encode("utf-8", errors="replace")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_event_input(
    label: str,
    resolution: Resolution,
    risk_level: str,
    status: str,
) -> None:
    if not label or not label.strip():
        raise ValueError("empty_label")
    if len(label.strip()) > 200:
        raise ValueError("label_too_long")
    if resolution.status != "resolved" or not resolution.kind or not resolution.start_at:
        raise ValueError("resolution_not_resolved")
    if risk_level not in ALLOWED_RISKS:
        raise ValueError("invalid_risk_level")
    if status not in ALLOWED_STATUSES:
        raise ValueError("invalid_status")
    if len(resolution.expression) > 500:
        raise ValueError("expression_too_long")


def _row_to_event(row: sqlite3.Row) -> dict[str, Any]:
    event = dict(row)
    event["is_current"] = bool(event["is_current"])
    event.pop("owner_key", None)
    return event


def _rank_events(events: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    normalized_query = _normalize_search_text(query)
    if not normalized_query:
        return events

    scored: list[tuple[int, int, dict[str, Any]]] = []
    for index, event in enumerate(events):
        label = _normalize_search_text(str(event.get("label") or ""))
        expression = _normalize_search_text(str(event.get("source_expression") or ""))
        score = 0
        if label and label in normalized_query:
            score += 20
        if expression and expression in normalized_query:
            score += 8
        for token in _search_tokens(label):
            if token in normalized_query:
                score += 2
        if score:
            scored.append((score, -index, event))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [event for _, _, event in scored]


def _normalize_search_text(text: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text.lower())


def _search_tokens(text: str) -> set[str]:
    if not text:
        return set()
    tokens = {text}
    if re.search(r"[\u4e00-\u9fff]", text):
        tokens.update(text[index : index + 2] for index in range(max(0, len(text) - 1)))
    else:
        tokens.update(token for token in re.split(r"\W+", text) if len(token) >= 3)
    return {token for token in tokens if len(token) >= 2}
