from __future__ import annotations

import logging
from typing import Optional
from celery import Task
from celery.utils.log import get_task_logger
from tuned.celery_app import celery_app

logger = get_task_logger(__name__)


def _fetch_country_code(ip: str) -> Optional[str]:
    """
    HTTP call to IP geolocation APIs. Max 2 attempts with graceful degradation.
    Returns ISO-3166-1 alpha-2 country code or None.
    """
    import httpx
    apis = [
        f"https://freeipapi.com/api/json/{ip}",
        f"http://ip-api.com/json/{ip}",
    ]
    for url in apis:
        try:
            resp = httpx.get(url, timeout=3.0)
            if resp.status_code == 429:
                logger.warning("[geolocation] Rate-limited by %s", url)
                break
            if resp.status_code == 200:
                data = resp.json()
                cc = data.get("countryCode") or data.get("country_code")
                if cc and len(cc) == 2:
                    return cc.upper()
        except Exception as exc:
            logger.warning("[geolocation] %s failed: %r", url, exc)
    return None


@celery_app.task(
    name="tuned.tasks.user_tasks.update_user_geolocation",
    bind=True,
    queue="notifications",
    max_retries=1,
    acks_late=True,
    soft_time_limit=15,
    time_limit=20,
)
def update_user_geolocation(self: Task, user_id: str, ip_address: str) -> None:
    """
    Resolve IP → country code and persist to user's localization preferences.
    Runs async so it never blocks the registration request path.
    """
    if not ip_address or ip_address in ("127.0.0.1", "localhost", "unknown"):
        return

    try:
        cc = _fetch_country_code(ip_address)
        if not cc:
            return

        from tuned.utils.dependencies import get_services
        from tuned.dtos import LocalizationUpdateDTO
        from tuned.dtos.base import BaseRequestDTO
        services = get_services()
        services.preferences.update_category(
            "localization",
            user_id,
            LocalizationUpdateDTO(country_code=cc),
            BaseRequestDTO(ip_address=ip_address),
        )
        logger.info(
            "[geolocation] Set country_code=%s for user %s", cc, user_id
        )
    except Exception as exc:
        logger.error(
            "[geolocation] Failed for user %s: %r", user_id, exc, exc_info=True
        )
        raise self.retry(exc=exc, countdown=60)
