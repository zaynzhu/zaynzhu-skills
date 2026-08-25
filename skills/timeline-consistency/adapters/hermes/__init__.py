"""Timeline Consistency Hermes Plugin。"""

from __future__ import annotations

from .schemas import TIMELINE_FORGET, TIMELINE_QUERY, TIMELINE_RESOLVE, TIMELINE_REVISE
from .service import TimelineService
from .storage import TimelineStore


PLUGIN_NAME = "timeline-consistency"


def register(ctx) -> None:
    from plugins.plugin_storage import plugin_db

    store = TimelineStore(plugin_db(PLUGIN_NAME))
    service = TimelineService(
        store,
        timezone_name=str(ctx.get_config("timezone", default="") or ""),
        retention_days=_as_int(ctx.get_config("retention_days", default=0), default=0),
        trust_remote_timestamps=_as_bool(
            ctx.get_config("trust_remote_timestamps", default=False),
            default=False,
        ),
    )

    ctx.on_unload(store.close)
    ctx.register_hook("pre_llm_call", service.pre_llm_call)
    ctx.register_tool(
        name="timeline_resolve",
        toolset="timeline_consistency",
        schema=TIMELINE_RESOLVE,
        handler=service.handle_resolve,
    )
    ctx.register_tool(
        name="timeline_query",
        toolset="timeline_consistency",
        schema=TIMELINE_QUERY,
        handler=service.handle_query,
    )
    ctx.register_tool(
        name="timeline_revise",
        toolset="timeline_consistency",
        schema=TIMELINE_REVISE,
        handler=service.handle_revise,
    )
    ctx.register_tool(
        name="timeline_forget",
        toolset="timeline_consistency",
        schema=TIMELINE_FORGET,
        handler=service.handle_forget,
    )


def _as_int(value, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return default
