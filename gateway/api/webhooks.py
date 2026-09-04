from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
import logging
from gateway.models.db import SessionLocal, WebhookEvent, Transaction
from gateway.config import get_config
from execution.service import ExecutionService

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    if not signature or not secret:
        return False
    expected_mac = hmac.new(
        secret.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_mac, signature)

@router.post("/v1/webhooks/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    config = get_config()
    signature = request.headers.get("x-razorpay-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
        
    raw_body = await request.body()
    
    if not verify_signature(raw_body, signature, config.webhook_secret):
        logger.error("Invalid Razorpay webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
        
    # We will deduplicate using the razorpay webhook event ID
    # But Razorpay might send an array or an object depending on the webhook type, usually it's an object with an `event` field.
    # In this webhook, the webhook payload usually looks like:
    # { "entity": "event", "account_id": "acc_...", "event": "payout.processed", "contains": ["payout"], "payload": { "payout": { "entity": { "id": "pout_...", "reference_id": "...", ... } } } }
    # To deduplicate across Razorpay events, razorpay webhooks don't always have a top level "id" but there is a header `x-razorpay-event-id` or we can deduplicate by the payout ID + event type.
    # Actually, Razorpay payload has an `event` field and we can dedupe on `x-razorpay-event-id`.
    event_id = request.headers.get("x-razorpay-event-id")
    event_type = payload.get("event")
    
    if not event_id:
        # Fallback deduplication ID
        event_id = hashlib.sha256(raw_body).hexdigest()
        
    # Idempotency check for webhook
    existing_event = db.query(WebhookEvent).filter_by(event_id=event_id).first()
    if existing_event:
        return {"status": "ok", "message": "already processed"}
        
    # Persist the event to ensure deduplication
    webhook_event = WebhookEvent(
        event_id=event_id,
        event_type=event_type or "unknown",
        payload=raw_body.decode()
    )
    db.add(webhook_event)
    db.commit()
    
    # Now process the payload for reconciliation
    if event_type in ["payout.processed", "payout.failed", "payout.reversed"]:
        payout_data = payload.get("payload", {}).get("payout", {}).get("entity", {})
        payout_id = payout_data.get("id")
        reference_id = payout_data.get("reference_id") # We mapped idempotency_key to nothing explicit except maybe we should set reference_id = idempotency_key. 
        # Wait, in RazorpayXClient we set `purpose: "payout"` and `notes`. We should also set `reference_id` to idempotency_key!
        # If we didn't, we can still reconcile if we stored razorpay_payout_id.
        
        # Let's find the transaction
        txn = None
        if payout_id:
            txn = db.query(Transaction).filter_by(razorpay_payout_id=payout_id).first()
        if not txn and reference_id:
            txn = db.query(Transaction).filter_by(txn_id=reference_id).first()
            
        if txn and txn.status not in ["SUCCEEDED", "FAILED"]:
            external_status = "SUCCEEDED" if event_type == "payout.processed" else "FAILED"
            service = ExecutionService()
            service.reconcile_spend(
                db=db, 
                idempotency_key=txn.txn_id, 
                external_status=external_status, 
                agent_id=txn.agent_id, 
                amount=txn.amount,
                payout_id=payout_id
            )
            
    return {"status": "ok"}
