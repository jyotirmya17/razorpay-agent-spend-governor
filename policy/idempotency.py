import hashlib
import json
from sqlalchemy.orm import Session
from gateway.models.db import IdempotencyRecord
from gateway.models.schemas import PayoutRequest

def hash_request(request: PayoutRequest) -> str:
    """Generate a deterministic hash of the request payload."""
    data = request.model_dump(exclude={"timestamp"})
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

def check_idempotency(db: Session, agent_id: str, idempotency_key: str, request: PayoutRequest):
    """
    Check if a request with this idempotency key has been processed or is processing.
    Using with_for_update() ensures that if another transaction has inserted this key
    but hasn't committed, we will wait for it to commit before reading it.
    Returns: (is_conflict, is_cached, cached_response)
    """
    req_hash = hash_request(request)
    record = db.query(IdempotencyRecord).filter(
        IdempotencyRecord.idempotency_key == idempotency_key
    ).with_for_update().first()
    
    if record:
        if record.request_hash != req_hash:
            return True, False, None
            
        if record.status == "PENDING":
            return True, False, None
            
        if record.status in ["COMPLETED", "FAILED"]:
            cached_response = json.loads(record.response_payload) if record.response_payload else {}
            return False, True, cached_response

    return False, False, None

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
