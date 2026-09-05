"""
seed_demo.py — Deterministic demo fixture seeder for Phase 4.7.

Agents seeded (demo-only; do NOT use in production):
  demo_normal_agent      — active mandate, normal transaction history
  demo_policy_agent      — active mandate with a very low txn_cap (triggers BLOCK)
  demo_behavior_agent    — active mandate, no transaction history (cold-start -> high anomaly)
  demo_provenance_agent  — active mandate, no provenance supplied in request
  demo_revocation_agent  — mandate will be revoked to demonstrate BLOCK on revocation

All amounts and IDs are synthetic.
No real Razorpay payout IDs are fabricated here.
"""
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway.models.db import SessionLocal, Base, engine, Agent, Mandate, MandateUsage, init_db


def seed():
    init_db()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        demo_agents = [
            ("demo_normal_agent",      "Demo Normal Agent"),
            ("demo_policy_agent",      "Demo Policy Agent"),
            ("demo_behavior_agent",    "Demo Behavior Agent"),
            ("demo_provenance_agent",  "Demo Provenance Agent"),
            ("demo_revocation_agent",  "Demo Revocation Agent"),
        ]

        for agent_id, name in demo_agents:
            if not db.query(Agent).filter_by(agent_id=agent_id).first():
                db.add(Agent(agent_id=agent_id, name=name, status="ACTIVE"))
        db.flush()

        mandates = [
            # (mandate_id, agent_id, daily_cap, weekly_cap, txn_cap, categories)
            ("man_demo_normal",      "demo_normal_agent",      500_000, 2_000_000, 500_000, ["cloud", "software", "vendor"]),
            ("man_demo_policy",      "demo_policy_agent",      500_000, 2_000_000,     100, ["cloud"]),  # txn_cap=1 INR -> BLOCK
            ("man_demo_behavior",    "demo_behavior_agent",    500_000, 2_000_000, 500_000, ["cloud", "software"]),
            ("man_demo_provenance",  "demo_provenance_agent",  500_000, 2_000_000, 500_000, ["cloud"]),
            ("man_demo_revocation",  "demo_revocation_agent",  500_000, 2_000_000, 500_000, ["cloud"]),
        ]

        for mandate_id, agent_id, daily_cap, weekly_cap, txn_cap, cats in mandates:
            if not db.query(Mandate).filter_by(mandate_id=mandate_id).first():
                db.add(Mandate(
                    mandate_id=mandate_id,
                    agent_id=agent_id,
                    version=1,
                    effective_from=now - timedelta(days=30),
                    expires_at=now + timedelta(days=365),
                    daily_cap=daily_cap,
                    weekly_cap=weekly_cap,
                    txn_cap=txn_cap,
                    allowed_categories=cats,
                    status="ACTIVE",
                ))
                db.add(MandateUsage(mandate_id=mandate_id, daily_usage=0, weekly_usage=0))

        db.commit()
        print("Demo fixtures seeded successfully.")
        print("Agents:", [a[0] for a in demo_agents])

    finally:
        db.close()


if __name__ == "__main__":
    seed()
