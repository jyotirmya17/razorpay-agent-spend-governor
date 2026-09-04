import os
import pytest

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("RAZORPAY_MODE", "test")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_mock")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "mock_secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "mock_webhook")
    monkeypatch.setenv("RAZORPAY_ACCOUNT_NUMBER", "7878780080316316")
