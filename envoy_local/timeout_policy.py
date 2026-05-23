"""Timeout policy definitions and validation for Envoy clusters and routes."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class TimeoutPolicy:
    connect_timeout_ms: int = 1000
    request_timeout_ms: Optional[int] = None
    idle_timeout_ms: Optional[int] = None
    max_stream_duration_ms: Optional[int] = None


@dataclass
class TimeoutValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def to_dict(policy: TimeoutPolicy) -> dict:
    d: dict = {"connect_timeout_ms": policy.connect_timeout_ms}
    if policy.request_timeout_ms is not None:
        d["request_timeout_ms"] = policy.request_timeout_ms
    if policy.idle_timeout_ms is not None:
        d["idle_timeout_ms"] = policy.idle_timeout_ms
    if policy.max_stream_duration_ms is not None:
        d["max_stream_duration_ms"] = policy.max_stream_duration_ms
    return d


def from_dict(data: dict) -> TimeoutPolicy:
    return TimeoutPolicy(
        connect_timeout_ms=data.get("connect_timeout_ms", 1000),
        request_timeout_ms=data.get("request_timeout_ms"),
        idle_timeout_ms=data.get("idle_timeout_ms"),
        max_stream_duration_ms=data.get("max_stream_duration_ms"),
    )


def validate_timeout_policy(policy: TimeoutPolicy) -> TimeoutValidationResult:
    result = TimeoutValidationResult()

    if policy.connect_timeout_ms <= 0:
        result.errors.append("connect_timeout_ms must be greater than 0")
    elif policy.connect_timeout_ms > 60_000:
        result.warnings.append("connect_timeout_ms exceeds 60s; this may cause slow failure detection")

    if policy.request_timeout_ms is not None:
        if policy.request_timeout_ms <= 0:
            result.errors.append("request_timeout_ms must be greater than 0")

    if policy.idle_timeout_ms is not None:
        if policy.idle_timeout_ms <= 0:
            result.errors.append("idle_timeout_ms must be greater than 0")

    if policy.max_stream_duration_ms is not None:
        if policy.max_stream_duration_ms <= 0:
            result.errors.append("max_stream_duration_ms must be greater than 0")
        if (
            policy.request_timeout_ms is not None
            and policy.max_stream_duration_ms < policy.request_timeout_ms
        ):
            result.warnings.append(
                "max_stream_duration_ms is less than request_timeout_ms; "
                "stream may be cut before request completes"
            )

    return result
