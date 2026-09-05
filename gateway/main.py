"""
Phase 4.7 FastAPI application entry point.
"""
import logging
from fastapi import FastAPI
from gateway.api.routes import router
from gateway.models.db import init_db

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Agent Spend Governor",
    description="Defense layer between autonomous AI agents and RazorpayX payouts.",
    version="4.7.0",
)

app.include_router(router)


@app.on_event("startup")
def startup():
    init_db()
