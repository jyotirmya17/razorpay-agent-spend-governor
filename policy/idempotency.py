import hashlib
import json
from sqlalchemy.orm import Session
from gateway.models.db import IdempotencyRecord
from gateway.models.schemas import PayoutRequest
from datetime import datetime, timezone

def hash_request(request: PayoutRequest) -> str:
    """Generate a deterministic hash of the request payload."""
    data = request.model_dump(exclude={"timestamp"})
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

import time

def check_idempotency(db: Session, agent_id: str, idempotency_key: str, request: PayoutRequest):
    """
    Check if a request with this idempotency key has been processed or is processing.
    Uses bounded polling with exponential backoff for PENDING status.
    Returns: (is_conflict, is_cached, cached_response, idempotency_status)
    """
    req_hash = hash_request(request)
    
    max_retries = 5
    base_delay = 0.5
    
    for attempt in range(max_retries):
        # We need to refresh the record from DB each time
        record = db.query(IdempotencyRecord).filter(
            IdempotencyRecord.idempotency_key == idempotency_key
        ).first()
        
        if not record:
            return False, False, None, "NOT_FOUND"
            
        if record.request_hash != req_hash:
            return True, False, None, "IDEMPOTENCY_KEY_CONFLICT"
            
        if record.status in ["COMPLETED", "FAILED"]:
            cached_response = json.loads(record.response_payload) if record.response_payload else {}
            return False, True, cached_response, record.status
            
        if record.status == "PENDING":
            # Check for stale PENDING (e.g. older than 2 minutes)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if (now - record.updated_at).total_seconds() > 120:
                # Stale pending: worker crashed, we can allow recovery
                return False, False, None, "STALE_PENDING"
                
            if attempt == max_retries - 1:
                return False, False, None, "UNKNOWN_IN_PROGRESS"
                
            # Bounded wait with exponential backoff
            time.sleep(base_delay * (2 ** attempt))
            db.expire(record) # Ensure fresh read next iteration
            
        elif record.status == "UNKNOWN":
            return False, False, None, "UNKNOWN_IN_PROGRESS"

    return False, False, None, "UNKNOWN_IN_PROGRESS"

def create_idempotency_record(db: Session, agent_id: str, idempotency_key: str, request: PayoutRequest):
    req_hash = hash_request(request)
    record = IdempotencyRecord(
        idempotency_key=idempotency_key,
        agent_id=agent_id,
        request_hash=req_hash,
        status="PENDING"
    )
    db.add(record)
    db.flush()
    return record
