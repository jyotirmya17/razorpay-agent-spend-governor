import os
import pytest
from pydantic import ValidationError
from gateway.config import RazorpayConfig, load_config

def test_valid_config():
    config = RazorpayConfig(
        mode="test",
        key_id="rzp_test_123",
        key_secret="secret",
        webhook_secret="webhook",
        account_number="123456"
    )
    assert config.mode == "test"
    assert config.key_id == "rzp_test_123"

def test_invalid_mode():
    with pytest.raises(ValidationError) as exc_info:
        RazorpayConfig(
            mode="live",
            key_id="rzp_test_123",
            key_secret="secret",
            webhook_secret="webhook",
            account_number="123456"
        )
    assert "RAZORPAY_MODE must be 'test'" in str(exc_info.value)

def test_invalid_key_id():
    with pytest.raises(ValidationError) as exc_info:
        RazorpayConfig(
            mode="test",
            key_id="rzp_live_123",
            key_secret="secret",
            webhook_secret="webhook",
            account_number="123456"
        )
    assert "RAZORPAY_KEY_ID must start with 'rzp_test_'" in str(exc_info.value)

def test_invalid_account_number_empty():
    with pytest.raises(ValidationError) as exc_info:
        RazorpayConfig(
            mode="test",
            key_id="rzp_test_123",
            key_secret="secret",
            webhook_secret="webhook",
            account_number="   "
        )
    assert "RAZORPAY_ACCOUNT_NUMBER must be set" in str(exc_info.value)

def test_invalid_account_number_missing():
    with pytest.raises(ValidationError):
        RazorpayConfig(
            mode="test",
            key_id="rzp_test_123",
            key_secret="secret",
            webhook_secret="webhook"
        )
