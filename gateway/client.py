import requests
from requests.auth import HTTPBasicAuth
import logging
from gateway.config import get_config

logger = logging.getLogger(__name__)

class RazorpayXClient:
    """Client for RazorpayX Payouts API"""

    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self):
        self.config = get_config()
        self.auth = HTTPBasicAuth(self.config.key_id, self.config.key_secret)
        self.timeout = 10  # Strict 10 second timeout

    def execute_payout(self, amount: int, currency: str, payee_id: str, idempotency_key: str, category: str, mode: str = "IMPS"):
        """
        Execute a payout using RazorpayX.
        Returns a tuple: (status: str, payload_or_error: dict)
        """
        url = f"{self.BASE_URL}/payouts"
        headers = {
            "Content-Type": "application/json",
            "X-Payout-Idempotency": idempotency_key
        }
        
        # In a real system, you might branch on payee_id format to decide fund_account_id vs contact_id.
        # Here we map payee_id directly to fund_account_id for simplicity, as defined in Razorpay API.
        payload = {
            "account_number": "7878780080316316", # Default test account from Razorpay docs
            "fund_account_id": payee_id,
            "amount": amount, # Razorpay expects amount in paise (100 paise = 1 INR)
            "currency": currency,
            "mode": mode,
            "purpose": "payout",
            "reference_id": idempotency_key,
            "notes": {
                "category": category
            }
        }

        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url, 
                    json=payload, 
                    headers=headers, 
                    auth=self.auth, 
                    timeout=self.timeout
                )
                
                # Map Response
                if 200 <= response.status_code < 300:
                    return "SUCCEEDED", response.json()
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt) # Exponential backoff: 1s, 2s
                        continue
                    else:
                        # Retries exhausted. Indeterminate external outcome.
                        return "UNKNOWN", response.json()
                elif 400 <= response.status_code < 500:
                    # 400, 401, 403, 404, 409, 422
                    return "FAILED", response.json()
                else:
                    # 5xx
                    return "UNKNOWN", {"error": f"HTTP {response.status_code}"}
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout executing payout for idempotency_key: {idempotency_key}")
                return "UNKNOWN", {"error": "Timeout"}
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error executing payout: {str(e)}")
                return "UNKNOWN", {"error": str(e)}

    def fetch_payout(self, payout_id: str):
        """Fallback reconciliation fetch"""
        url = f"{self.BASE_URL}/payouts/{payout_id}"
        try:
            response = requests.get(url, auth=self.auth, timeout=self.timeout)
            if 200 <= response.status_code < 300:
                data = response.json()
                status = data.get("status")
                # Map razorpay statuses
                if status in ["processed", "reversed"]:
                    return "SUCCEEDED" if status == "processed" else "FAILED", data
                elif status in ["pending", "processing", "queued"]:
                    return "UNKNOWN", data
                else:
                    return "FAILED", data
            return "UNKNOWN", {"error": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException:
            return "UNKNOWN", {"error": "Fetch failed"}
