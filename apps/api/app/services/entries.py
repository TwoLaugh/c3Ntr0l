import json
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.entry import Entry
from app.models.enums import EntryActor, EntrySource


def create_entry(
    db: Session,
    *,
    user_id: UUID,
    source_type: EntrySource,
    raw_text: str,
    source_id: UUID | None = None,
    actor: EntryActor = EntryActor.user,
    metadata: dict | None = None,
    ai_interpretation: dict | None = None,
) -> Entry:
    entry = Entry(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        actor=actor,
        raw_text=raw_text,
        metadata_json=metadata or {},
        ai_interpretation=ai_interpretation,
    )
    db.add(entry)
    db.flush()
    return entry


def serialize_entry_payload(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
