"""
Data Transfer Objects for health check responses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CheckStatus(str, Enum):
    OK = "ok"
    WARN = "warn"
    DEGRADED = "degraded"
    ERROR = "error"

@dataclass(frozen=True)
class DependencyCheckResult:
    status: CheckStatus
    latency_ms: float

    def is_healthy(self) -> bool:
        return self.status in (CheckStatus.OK, CheckStatus.WARN)


@dataclass(frozen=True)
class DependencyCheckError:
    status: CheckStatus
    error: str
    latency_ms: float

    def is_healthy(self) -> bool:
        return False

@dataclass(frozen=True)
class DiskCheckResult:
    status: CheckStatus
    used_pct: float

    def is_healthy(self) -> bool:
        return self.status in (CheckStatus.OK, CheckStatus.WARN)

@dataclass(frozen=True)
class DiskCheckError:
    status: CheckStatus
    error: str

    def is_healthy(self) -> bool:
        return False

PostgresResult = DependencyCheckResult | DependencyCheckError
RedisResult = DependencyCheckResult | DependencyCheckError
DiskResult = DiskCheckResult | DiskCheckError

@dataclass(frozen=True)
class HealthResponse:
    status: CheckStatus
    uptime_seconds: float
    postgres: PostgresResult
    redis: RedisResult
    disk: DiskResult

    def to_dict(self) -> dict[str, object]:
        def _result_to_dict(
            r: PostgresResult | RedisResult | DiskResult,
        ) -> dict[str, object]:
            return {k: (v.value if isinstance(v, CheckStatus) else v) for k, v in r.__dict__.items()}

        return {
            "status": self.status.value,
            "uptime_seconds": self.uptime_seconds,
            "checks": {
                "postgres": _result_to_dict(self.postgres),
                "redis": _result_to_dict(self.redis),
                "disk": _result_to_dict(self.disk),
            },
        }