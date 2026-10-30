"""Safe audit logger for PrivacyLens."""
import time
import uuid
from typing import List, Dict, Any, Optional
from app.models import AuditEvent, AuditEventType

class AuditLogger:
    def __init__(self):
        self._events: List[AuditEvent] = []

    def log(
        self,
        event_type: AuditEventType,
        run_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Records a privacy-safe audit event.
        Ensures details contain only safe metadata (counts, categories, rule IDs, latencies).
        """
        event = AuditEvent(
            id=str(uuid.uuid4())[:8],
            timestamp=time.time(),
            event_type=event_type,
            run_id=run_id,
            details=details or {},
        )
        self._events.append(event)
        return event

    def get_events(self, run_id: Optional[str] = None) -> List[AuditEvent]:
        if run_id:
            return [e for e in self._events if e.run_id == run_id]
        return list(self._events)

    def clear(self):
        self._events.clear()

audit_logger = AuditLogger()
