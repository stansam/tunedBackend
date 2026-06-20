import logging
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from flask import current_app
from datetime import datetime, timezone

from tuned.redis_client import get_redis_client
from tuned.dtos.payment import (
    PesapalSubmitOrderDTO,
    PesapalSubmitOrderResponseDTO,
    PesapalTransactionStatusDTO,
)

logger = logging.getLogger(__name__)

# Known Pesapal IP ranges for IPN signature/IP verification
PESAPAL_IPN_ALLOWED_IPS: frozenset[str] = frozenset({
    "196.201.214.200",
    "196.201.214.206",
    "196.201.213.114",
    "196.201.214.115",
})

class PesapalHelper:
    def __init__(self) -> None:
        self.sandbox = current_app.config.get("PESAPAL_SANDBOX", True)
        self.base_url = "https://cybqa.pesapal.com/pesapalv3" if self.sandbox else "https://pay.pesapal.com/v3"
        self.consumer_key = current_app.config.get("PESAPAL_CONSUMER_KEY", "")
        self.consumer_secret = current_app.config.get("PESAPAL_CONSUMER_SECRET", "")
        self.ipn_url = current_app.config.get("PESAPAL_IPN_URL", "")
        self.callback_url = current_app.config.get("PESAPAL_CALLBACK_URL", "")

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
        Uses Redis client for multi-worker support.
        """
        r = get_redis_client()
        cached_token = r.get("pesapal:token")
        if cached_token:
            logger.info("Found cached Pesapal token in Redis.")
            return str(cached_token)

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
            
            now = datetime.now(timezone.utc).timestamp()
            ttl_seconds = 270
            if expiry:
                try:
                    if isinstance(expiry, str):
                        dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                        ttl_seconds = int(dt.timestamp() - now)
                    else:
                        ttl_seconds = int(float(expiry) - now)
                except Exception:
                    ttl_seconds = 270
            
            # buffer room: subtract 60 seconds from TTL so we don't use an expired token
            ttl_seconds = max(30, ttl_seconds - 60)
            
            # Cache the token in Redis
            r.setex("pesapal:token", ttl_seconds, token)
            logger.info("Successfully fetched and cached new Pesapal JWT token in Redis.")
            return str(token)
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

    def submit_order(self, data: PesapalSubmitOrderDTO) -> PesapalSubmitOrderResponseDTO:
        """
        Submits a payment order to Pesapal V3 and returns a typed response DTO.
        """
        token = self.get_token()
        ipn_id = self.register_ipn(token)

        url = f"{self.base_url}/api/Transactions/SubmitOrderRequest"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "id": data.merchant_reference,
            "currency": data.currency,
            "amount": data.amount,
            "description": data.description,
            "callback_url": self.callback_url,
            "notification_id": ipn_id,
            "billing_address": {
                "email_address": data.email or "",
                "phone_number": data.phone or "0700000000",
                "first_name": data.first_name or "Client",
                "last_name": data.last_name or "User",
                "country_code": "KE",
            }
        }

        try:
            response = self._make_session().post(url, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            res = response.json()
        except Exception as e:
            logger.error("[PesapalHelper.submit_order] Request failed: %r", e)
            raise

        redirect_url = res.get("redirect_url")
        order_tracking_id = res.get("order_tracking_id")

        if not redirect_url or not order_tracking_id:
            raise ValueError(
                f"[PesapalHelper.submit_order] Unexpected Pesapal response — "
                f"missing redirect_url or order_tracking_id: {res}"
            )

        logger.info(
            "[PesapalHelper.submit_order] Order submitted. Ref=%s, TrackingId=%s",
            data.merchant_reference, order_tracking_id
        )

        return PesapalSubmitOrderResponseDTO(
            redirect_url=redirect_url,
            order_tracking_id=order_tracking_id,
            merchant_reference=data.merchant_reference,
        )

    def get_transaction_status(self, order_tracking_id: str) -> PesapalTransactionStatusDTO:
        """
        Queries Pesapal for the authoritative transaction status.
        """
        token = self.get_token()
        url = f"{self.base_url}/api/Transactions/GetTransactionStatus"
        params = {"orderTrackingId": order_tracking_id}
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        try:
            response = self._make_session().get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            res = response.json()
        except Exception as e:
            logger.error("[PesapalHelper.get_transaction_status] Request failed: %r", e)
            raise

        return PesapalTransactionStatusDTO(
            payment_status_description=str(res.get("payment_status_description", "")).lower(),
            amount=float(res.get("amount", 0.0)),
            currency=str(res.get("currency", "USD")),
            payment_method=res.get("payment_method"),
            order_tracking_id=str(res.get("order_tracking_id", order_tracking_id)),
            merchant_reference=str(res.get("merchant_reference", "")),
        )
