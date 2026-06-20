from __future__ import annotations

import os
import time
from typing import cast
import psycopg2
import psycopg2.extensions
import redis as redis_lib
from redis import Redis

from tuned.redis_client import get_redis_client
from tuned.dtos.health import (
    CheckStatus,
    DependencyCheckError,
    DependencyCheckResult,
    DiskCheckError,
    DiskCheckResult,
    DiskResult,
    PostgresResult,
    RedisResult,
)

_DISK_WARN_THRESHOLD_PCT: float = 85.0
_LATENCY_WARN_THRESHOLD_MS: float = 200.0


class PostgresHealthChecker:
    """
    Opens a real psycopg2 connection, executes SELECT 1, and measures
    round-trip latency.
    """
    def run(self) -> PostgresResult:
        start: float = time.monotonic()
        conn: psycopg2.extensions.connection | None = None
        try:
            conn = psycopg2.connect(
                host=os.environ["DB_HOST"],
                port=int(os.environ.get("DB_PORT", "5432")),
                dbname=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                connect_timeout=3,
                options="-c statement_timeout=3000",
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            latency_ms: float = round((time.monotonic() - start) * 1000, 2)
            status = (
                CheckStatus.WARN
                if latency_ms > _LATENCY_WARN_THRESHOLD_MS
                else CheckStatus.OK
            )
            return DependencyCheckResult(status=status, latency_ms=latency_ms)
        except psycopg2.OperationalError as exc:
            return DependencyCheckError(
                status=CheckStatus.ERROR,
                error=f"OperationalError: {exc}",
                latency_ms=round((time.monotonic() - start) * 1000, 2),
            )
        except psycopg2.Error as exc:
            return DependencyCheckError(
                status=CheckStatus.ERROR,
                error=f"PostgresError: {exc}",
                latency_ms=round((time.monotonic() - start) * 1000, 2),
            )
        except Exception as exc:
            return DependencyCheckError(
                status=CheckStatus.ERROR,
                error=f"UnexpectedError: {exc}",
                latency_ms=round((time.monotonic() - start) * 1000, 2),
            )
        finally:
            if conn is not None and not conn.closed:
                conn.close()


class RedisHealthChecker:
    """
    Sends PING and measures round-trip latency.
    """
    def __init__(self) -> None:
        self._client: Redis = get_redis_client()

    def run(self) -> RedisResult:
        start: float = time.monotonic()
        try:
            response: bool = cast(bool, self._client.ping())
            latency_ms: float = round((time.monotonic() - start) * 1000, 2)

            if not response:
                return DependencyCheckError(
                    status=CheckStatus.ERROR,
                    error="PING returned False",
                    latency_ms=latency_ms,
                )

            status = (
                CheckStatus.WARN
                if latency_ms > _LATENCY_WARN_THRESHOLD_MS
                else CheckStatus.OK
            )
            return DependencyCheckResult(status=status, latency_ms=latency_ms)
        except redis_lib.AuthenticationError as exc:
            return DependencyCheckError(
                status=CheckStatus.ERROR,
                error=f"AuthenticationError: {exc}",
                latency_ms=round((time.monotonic() - start) * 1000, 2),
            )
        except redis_lib.ConnectionError as exc:
            return DependencyCheckError(
                status=CheckStatus.ERROR,
                error=f"ConnectionError: {exc}",
                latency_ms=round((time.monotonic() - start) * 1000, 2),
            )
        except redis_lib.TimeoutError as exc:
            return DependencyCheckError(
                status=CheckStatus.ERROR,
                error=f"TimeoutError: {exc}",
                latency_ms=round((time.monotonic() - start) * 1000, 2),
            )
        except Exception as exc:
            return DependencyCheckError(
                status=CheckStatus.ERROR,
                error=f"UnexpectedError: {exc}",
                latency_ms=round((time.monotonic() - start) * 1000, 2),
            )


class DiskHealthChecker:
    """
    Checks the uploads volume partition and warns if exceeds space.
    """
    def __init__(self, path: str | None = None) -> None:
        self._path: str = (
            path
            or os.environ.get("UPLOAD_ROOT", "/home/vault/tunedBundle/uploads")
        )

    def run(self) -> DiskResult:
        try:
            stat: os.statvfs_result = os.statvfs(self._path)
            total: int = stat.f_blocks * stat.f_frsize
            free: int = stat.f_bfree * stat.f_frsize
            used_pct: float = round((1 - free / total) * 100, 1) if total > 0 else 0.0
            status = CheckStatus.WARN if used_pct > _DISK_WARN_THRESHOLD_PCT else CheckStatus.OK
            return DiskCheckResult(status=status, used_pct=used_pct)
        except PermissionError as exc:
            return DiskCheckError(status=CheckStatus.ERROR, error=f"PermissionError: {exc}")
        except FileNotFoundError as exc:
            return DiskCheckError(status=CheckStatus.ERROR, error=f"PathNotFound: {exc}")
        except OSError as exc:
            return DiskCheckError(status=CheckStatus.ERROR, error=f"OSError: {exc}")
        except Exception as exc:
            return DiskCheckError(
                status=CheckStatus.ERROR,
                error=f"UnexpectedError: {exc}",
            )