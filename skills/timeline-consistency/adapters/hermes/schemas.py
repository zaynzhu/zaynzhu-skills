"""Hermes Plugin 工具 schema。"""

TIMELINE_RESOLVE = {
    "name": "timeline_resolve",
    "description": (
        "把当前用户消息中的相对时间绑定到该消息的原始发送时间，并创建时间线事件。"
        "涉及计划、承诺、截止时间、已发生事件或重要相对日期时，在最终回答前调用。"
        "不要传入或猜测 source timestamp；Plugin 会从 Hermes 当轮 metadata 读取。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "label": {"type": "string", "maxLength": 200, "description": "简短事件名，例如“请假”"},
            "expression": {"type": "string", "maxLength": 500, "description": "用户原始时间短语，例如“明天”"},
            "risk_level": {
                "type": "string",
                "enum": ["low", "high"],
                "description": "可能影响现实行动或造成损失时为 high",
            },
            "status": {
                "type": "string",
                "enum": ["planned", "historical"],
                "description": "未来安排用 planned，已经发生的事件用 historical",
            },
            "confirmation_token": {
                "type": "string",
                "description": "只有用户明确确认上一轮候选后才传回",
            },
            "confirmed": {
                "type": "boolean",
                "description": "只有用户明确确认候选时设为 true",
            },
        },
        "required": [],
        "additionalProperties": False,
    },
}

TIMELINE_QUERY = {
    "name": "timeline_query",
    "description": (
        "查询当前用户的事件账本。回答最近安排、寻找待修订事件或核对来源时调用。"
        "返回多个合理候选时必须让用户选择，不能静默使用最近一条。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "事件关键词，可为空"},
            "include_history": {
                "type": "boolean",
                "description": "是否包含被后续版本取代的历史版本",
            },
            "limit": {"type": "integer", "minimum": 1, "maximum": 50},
        },
        "additionalProperties": False,
    },
}

TIMELINE_REVISE = {
    "name": "timeline_revise",
    "description": (
        "修订一个精确事件版本：改期、完成或取消。每次调用生成新版本并保留 supersedes 关系。"
        "调用前先用 timeline_query 找到唯一 current event_id。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "event_id": {"type": "string", "description": "唯一当前事件版本 ID"},
            "expression": {"type": "string", "maxLength": 500, "description": "新的用户原始时间短语；状态变化时可省略"},
            "label": {"type": "string", "maxLength": 200, "description": "新的事件名；不修改时省略"},
            "status": {
                "type": "string",
                "enum": ["planned", "completed", "cancelled", "historical"],
            },
            "risk_level": {"type": "string", "enum": ["low", "high"]},
            "confirmation_token": {
                "type": "string",
                "description": "只有用户明确确认上一轮候选后才传回",
            },
            "confirmed": {
                "type": "boolean",
                "description": "只有用户明确确认候选时设为 true",
            },
        },
        "required": [],
        "additionalProperties": False,
    },
}

TIMELINE_FORGET = {
    "name": "timeline_forget",
    "description": (
        "永久删除一个事件的全部版本。只有用户明确要求忘记或删除该事件时调用；"
        "调用前必须用 timeline_query 得到精确 event_id。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "event_id": {"type": "string", "description": "事件任一版本 ID"},
            "user_confirmed_forget": {
                "type": "boolean",
                "description": "用户明确要求忘记时必须为 true",
            },
        },
        "required": ["event_id", "user_confirmed_forget"],
        "additionalProperties": False,
    },
}
