from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log(
    db: Session,
    action: str,
    user_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_=metadata,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    return entry
