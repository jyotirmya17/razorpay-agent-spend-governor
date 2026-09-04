import os
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

load_dotenv()

class RazorpayConfig(BaseModel):
    mode: str = Field(default="test")
    key_id: str = Field(...)
    key_secret: str = Field(...)
    webhook_secret: str = Field(...)
    account_number: str = Field(...)

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

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("RAZORPAY_ACCOUNT_NUMBER must be set.")
        return v

def load_config() -> RazorpayConfig:
    """Load and strictly validate Razorpay configuration."""
    # If environment variables are missing (like in test environments), we will raise ValidationError
    return RazorpayConfig(
        mode=os.environ.get("RAZORPAY_MODE", "test"),
        key_id=os.environ.get("RAZORPAY_KEY_ID", "rzp_test_dummy"),
        key_secret=os.environ.get("RAZORPAY_KEY_SECRET", "dummy_secret"),
        webhook_secret=os.environ.get("RAZORPAY_WEBHOOK_SECRET", "dummy_webhook_secret"),
        account_number=os.environ.get("RAZORPAY_ACCOUNT_NUMBER")
    )

def get_config() -> RazorpayConfig:
    return load_config()
