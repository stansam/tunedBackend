import logging
import requests
import threading
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from flask import current_app
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Known Pesapal IP ranges for IPN signature/IP verification
PESAPAL_IPN_ALLOWED_IPS: frozenset[str] = frozenset({
    "196.201.214.200",
    "196.201.214.206",
    "196.201.213.114",
    "196.201.214.115",
})

class PesapalHelper:
    # Class-level variables for thread-safe in-memory token cache
    _token: str | None = None
    _token_expires: float | None = None
    _token_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self.sandbox = current_app.config.get("PESAPAL_SANDBOX", True)
        self.base_url = "https://cybqa.pesapal.com/pesapalv3" if self.sandbox else "https://pay.pesapal.com/v3"
        self.consumer_key = current_app.config.get("PESAPAL_CONSUMER_KEY", "")
        self.consumer_secret = current_app.config.get("PESAPAL_CONSUMER_SECRET", "")
        self.ipn_url = current_app.config.get("PESAPAL_IPN_URL", "")

    def _make_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,        # 0.5s, 1.0s, 2.0s
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def get_token(self) -> str:
        """
        Authenticate with Pesapal and retrieve a JWT bearer token.
        """
        now = datetime.now(timezone.utc).timestamp()
        with PesapalHelper._token_lock:
            if PesapalHelper._token and PesapalHelper._token_expires and now < PesapalHelper._token_expires:
                return PesapalHelper._token

            url = f"{self.base_url}/api/Auth/RequestToken"
            payload = {
                "consumer_key": self.consumer_key,
                "consumer_secret": self.consumer_secret
            }
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            try:
                logger.info(f"Authenticating with Pesapal API: {url}")
                session = self._make_session()
                response = session.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                res_data = response.json()
                logger.info(f"Pesapal auth response: {res_data}")
                token = res_data.get("token")
                expiry = res_data.get("expiryDate")
                if not token:
                    raise ValueError("No token returned from Pesapal auth endpoint")
                
                PesapalHelper._token = token
                if expiry:
                    try:
                        if isinstance(expiry, str):
                            dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                            PesapalHelper._token_expires = dt.timestamp()
                        else:
                            PesapalHelper._token_expires = float(expiry)
                    except Exception:
                        PesapalHelper._token_expires = now + 270
                else:
                    PesapalHelper._token_expires = now + 270
                
                logger.info("Successfully fetched and cached new Pesapal JWT token.")
                return token
            except Exception as e:
                logger.error(f"Pesapal Authentication failed: {str(e)}")
                raise

    def get_registered_ipns(self, token: str) -> list:
        """
        Get all registered IPNs from Pesapal to avoid duplicate registration.
        """
        url = f"{self.base_url}/api/URLSetup/GetIpnList"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        try:
            session = self._make_session()
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch Pesapal IPN list: {str(e)}")
            return []

    def register_ipn(self, token: str) -> str:
        """
        Register our IPN URL, reusing an existing registration if possible.
        """
        existing_ipns = self.get_registered_ipns(token)
        for ipn in existing_ipns:
            if ipn.get("url") == self.ipn_url:
                logger.info(f"Reusing existing Pesapal IPN ID: {ipn.get('ipn_id')}")
                return ipn.get("ipn_id")

        url = f"{self.base_url}/api/URLSetup/RegisterIPN"
        payload = {
            "url": self.ipn_url,
            "ipn_notification_type": "GET"
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        try:
            logger.info(f"Registering new Pesapal IPN URL: {self.ipn_url}")
            session = self._make_session()
            response = session.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            res_data = response.json()
            ipn_id = res_data.get("ipn_id")
            if not ipn_id:
                raise ValueError("No ipn_id returned from Pesapal RegisterIPN endpoint")
            logger.info(f"Successfully registered new Pesapal IPN ID: {ipn_id}")
            return ipn_id
        except Exception as e:
            logger.error(f"Failed to register Pesapal IPN URL: {str(e)}")
            raise

    def submit_order(self, order_id: str, amount: float, email: str, phone: str, first_name: str, last_name: str, description: str = "") -> dict:
        """
        Submit a new order transaction request to Pesapal and get the payment page URL.
        """
        token = self.get_token()
        ipn_id = self.register_ipn(token)
        callback_url = current_app.config.get("PESAPAL_CALLBACK_URL", "")

        url = f"{self.base_url}/api/Transactions/SubmitOrderRequest"
        payload = {
            "id": order_id,
            "currency": "USD",
            "amount": amount,
            "description": description or f"Payment for Order #{order_id}",
            "callback_url": callback_url,
            "notification_id": ipn_id,
            "billing_address": {
                "email_address": email,
                "phone_number": phone or "0700000000",
                "country_code": "KE",
                "first_name": first_name or "Client",
                "last_name": last_name or "User",
                "line_1": "",
                "line_2": "",
                "city": "",
                "state": "",
                "postal_code": "",
                "zip_code": ""
            }
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        try:
            logger.info(f"Submitting Pesapal transaction request for order {order_id} (Amount: {amount})")
            session = self._make_session()
            response = session.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Pesapal transaction submission failed: {str(e)}")
            raise

    def get_transaction_status(self, order_tracking_id: str) -> dict:
        """
        Verify transaction status from Pesapal.
        """
        token = self.get_token()
        url = f"{self.base_url}/api/Transactions/GetTransactionStatus"
        params = {"orderTrackingId": order_tracking_id}
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        try:
            logger.info(f"Fetching Pesapal transaction status for tracking ID: {order_tracking_id}")
            session = self._make_session()
            response = session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch Pesapal transaction status: {str(e)}")
            raise
