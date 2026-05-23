"""Retry policy configuration and validation for Envoy routes."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


RETRY_ON_CONDITIONS = [
    "5xx",
    "gateway-error",
    "reset",
    "connect-failure",
    "retriable-4xx",
    "refused-stream",
    "retriable-status-codes",
]


@dataclass
class RetryPolicy:
    retry_on: List[str] = field(default_factory=lambda: ["5xx"])
    num_retries: int = 3
    per_try_timeout_ms: Optional[int] = None
    retriable_status_codes: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "retry_on": ",".join(self.retry_on),
            "num_retries": self.num_retries,
        }
        if self.per_try_timeout_ms is not None:
            d["per_try_timeout"] = f"{self.per_try_timeout_ms}ms"
        if self.retriable_status_codes:
            d["retriable_status_codes"] = self.retriable_status_codes
        return d

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "RetryPolicy":
        retry_on = data.get("retry_on", "5xx").split(",")
        retry_on = [r.strip() for r in retry_on if r.strip()]
        return RetryPolicy(
            retry_on=retry_on,
            num_retries=int(data.get("num_retries", 3)),
            per_try_timeout_ms=_parse_timeout_ms(data.get("per_try_timeout")),
            retriable_status_codes=data.get("retriable_status_codes", []),
        )


def _parse_timeout_ms(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    value = value.strip()
    if value.endswith("ms"):
        return int(value[:-2])
    if value.endswith("s"):
        return int(value[:-1]) * 1000
    return int(value)


def validate_retry_policy(policy: RetryPolicy) -> List[str]:
    """Return a list of validation error strings, empty if valid."""
    errors: List[str] = []
    for condition in policy.retry_on:
        if condition not in RETRY_ON_CONDITIONS:
            errors.append(f"Unknown retry_on condition: '{condition}'")
    if policy.num_retries < 0:
        errors.append("num_retries must be non-negative")
    if policy.per_try_timeout_ms is not None and policy.per_try_timeout_ms <= 0:
        errors.append("per_try_timeout_ms must be positive")
    if "retriable-status-codes" in policy.retry_on and not policy.retriable_status_codes:
        errors.append("retriable_status_codes must be set when using 'retriable-status-codes'")
    return errors
