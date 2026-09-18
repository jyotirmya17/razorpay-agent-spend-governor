from fastapi.testclient import TestClient
from gateway.main import app

client = TestClient(app)

from gateway.models.db import init_db

def test_rate_limiting():
    init_db()
    from gateway.api.routes import limiter
    limiter.enabled = True
    try:
        success_count = 0
        rate_limited = False
        
        for i in range(35):
            resp = client.post("/v1/demo/scenario/1")
            if resp.status_code == 200:
                success_count += 1
            elif resp.status_code == 429:
                rate_limited = True
                break
                
        assert rate_limited, "Rate limit of 30/minute was not enforced"
        assert success_count <= 30, "Too many requests succeeded"
    finally:
        limiter.enabled = False
