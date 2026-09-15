"""
Phase 4.7 FastAPI application entry point.
"""
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gateway.api.routes import router
from gateway.models.db import init_db
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from gateway.api.routes import router, limiter

if "pytest" in sys.modules:
    limiter.enabled = False

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Agent Spend Governor",
    description="Defense layer between autonomous AI agents and RazorpayX payouts.",
    version="5.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "https://razorpay-agent-spend-governor.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup():
    init_db()
