from __future__ import annotations

import os
import time
from typing import ClassVar

from flask import Blueprint, Response, jsonify, request
from flask.views import MethodView

from tuned.health.checkers import DiskHealthChecker, PostgresHealthChecker, RedisHealthChecker
from tuned.dtos.health import CheckStatus, HealthResponse, PostgresResult, RedisResult, DiskResult

health_bp: Blueprint = Blueprint("health", __name__)

_PROCESS_START: float = time.time()

_HEALTH_TOKEN_HEADER: str = "X-Health-Token"
_HEALTH_TOKEN_ENV_KEY: str = "HEALTH_CHECK_TOKEN"


def _is_authorised() -> bool:
    expected: str | None = os.environ.get(_HEALTH_TOKEN_ENV_KEY)
    if not expected:
        return False
    provided: str | None = request.headers.get(_HEALTH_TOKEN_HEADER)
    if not provided:
        return False
    import hmac
    return hmac.compare_digest(provided.strip(), expected.strip())


def _secure_response(payload: dict[str, object], status_code: int) -> Response:
    resp: Response = jsonify(payload)
    resp.status_code = status_code
    resp.headers["Server"] = "unknown"
    resp.headers.pop("X-Powered-By", None)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Pragma"] = "no-cache"
    return resp

class HealthView(MethodView):
    """
    GET /health

    Runs all dependency probes and returns a structured HealthResponse.
    HTTP 200 → all critical deps healthy.
    HTTP 503 → postgres or redis is down (Docker will restart the container).
    HTTP 401 → missing or invalid probe token.

    Only GET is allowed; all other verbs return 405.
    """

    init_every_request: ClassVar[bool] = False

    def __init__(self) -> None:
        self._postgres_checker = PostgresHealthChecker()
        self._redis_checker = RedisHealthChecker()
        self._disk_checker = DiskHealthChecker()

    def get(self) -> Response:
        if not _is_authorised():
            return _secure_response({"detail": "Unauthorised"}, 401)

        postgres_result: PostgresResult = self._postgres_checker.run()
        redis_result: RedisResult = self._redis_checker.run()
        disk_result: DiskResult = self._disk_checker.run()

        critical_healthy: bool = postgres_result.is_healthy() and redis_result.is_healthy()

        overall_status: CheckStatus = (
            CheckStatus.OK if critical_healthy else CheckStatus.DEGRADED
        )

        response_dto: HealthResponse = HealthResponse(
            status=overall_status,
            uptime_seconds=round(time.time() - _PROCESS_START, 1),
            postgres=postgres_result,
            redis=redis_result,
            disk=disk_result,
        )

        http_status: int = 200 if critical_healthy else 503
        return _secure_response(response_dto.to_dict(), http_status)


health_bp.add_url_rule(
    "/health",
    view_func=HealthView.as_view("health"),
    methods=["GET"],
)