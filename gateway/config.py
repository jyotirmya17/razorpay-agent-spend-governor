import os
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

load_dotenv()

class RazorpayConfig(BaseModel):
    mode: str = Field(default="test")
    key_id: str = Field(...)
    key_secret: str = Field(...)
    webhook_secret: str = Field(...)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v.lower() != "test":
            raise ValueError("RAZORPAY_MODE must be 'test'. Live execution is blocked.")
        return v.lower()

    @field_validator("key_id")
    @classmethod
    def validate_key_id(cls, v: str) -> str:
        if not v.startswith("rzp_test_"):
            raise ValueError("RAZORPAY_KEY_ID must start with 'rzp_test_'. Live keys are prohibited.")
        return v

def load_config() -> RazorpayConfig:
    """Load and strictly validate Razorpay configuration."""
    # If environment variables are missing (like in test environments), we will raise ValidationError
    return RazorpayConfig(
        mode=os.environ.get("RAZORPAY_MODE", "test"),
        key_id=os.environ.get("RAZORPAY_KEY_ID", "rzp_test_dummy"),
        key_secret=os.environ.get("RAZORPAY_KEY_SECRET", "dummy_secret"),
        webhook_secret=os.environ.get("RAZORPAY_WEBHOOK_SECRET", "dummy_webhook_secret")
    )

def get_config() -> RazorpayConfig:
    return load_config()
