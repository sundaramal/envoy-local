"""Circuit breaker threshold configuration and validation for Envoy clusters."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class CircuitBreakerThresholds:
    max_connections: int = 1024
    max_pending_requests: int = 1024
    max_requests: int = 1024
    max_retries: int = 3
    max_connection_pools: Optional[int] = None

    def to_dict(self) -> dict:
        d = {
            "max_connections": self.max_connections,
            "max_pending_requests": self.max_pending_requests,
            "max_requests": self.max_requests,
            "max_retries": self.max_retries,
        }
        if self.max_connection_pools is not None:
            d["max_connection_pools"] = self.max_connection_pools
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "CircuitBreakerThresholds":
        return cls(
            max_connections=data.get("max_connections", 1024),
            max_pending_requests=data.get("max_pending_requests", 1024),
            max_requests=data.get("max_requests", 1024),
            max_retries=data.get("max_retries", 3),
            max_connection_pools=data.get("max_connection_pools"),
        )


@dataclass
class ValidationError:
    field: str
    message: str


@dataclass
class CircuitBreakerValidationResult:
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, field: str, message: str) -> None:
        self.errors.append(ValidationError(field=field, message=message))


def validate_circuit_breaker(thresholds: CircuitBreakerThresholds) -> CircuitBreakerValidationResult:
    result = CircuitBreakerValidationResult()
    if thresholds.max_connections <= 0:
        result.add_error("max_connections", "must be greater than 0")
    if thresholds.max_pending_requests <= 0:
        result.add_error("max_pending_requests", "must be greater than 0")
    if thresholds.max_requests <= 0:
        result.add_error("max_requests", "must be greater than 0")
    if thresholds.max_retries < 0:
        result.add_error("max_retries", "must be non-negative")
    if thresholds.max_connection_pools is not None and thresholds.max_connection_pools <= 0:
        result.add_error("max_connection_pools", "must be greater than 0 if set")
    return result


def format_circuit_breaker_report(thresholds: CircuitBreakerThresholds, result: CircuitBreakerValidationResult) -> str:
    lines = ["Circuit Breaker Thresholds:"]
    for k, v in thresholds.to_dict().items():
        lines.append(f"  {k}: {v}")
    if result.is_valid:
        lines.append("Validation: OK")
    else:
        lines.append("Validation: FAILED")
        for err in result.errors:
            lines.append(f"  [ERROR] {err.field}: {err.message}")
    return "\n".join(lines)
