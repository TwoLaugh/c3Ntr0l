from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.ai_action_log import AIActionLog
from app.models.enums import SourceType


def log_action(
    db: Session,
    *,
    user_id: UUID,
    source_type: SourceType,
    action_type: str,
    target_type: str,
    target_id: UUID | None = None,
    source_id: UUID | None = None,
    before_state: dict | None = None,
    after_state: dict | None = None,
    reason: str | None = None,
    reversible: bool = False,
) -> AIActionLog:
    action = AIActionLog(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        before_state=_json_ready(before_state),
        after_state=_json_ready(after_state),
        reason=reason,
        reversible=reversible,
    )
    db.add(action)
    return action


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    return value
