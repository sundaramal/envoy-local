"""Header rewrite rules for Envoy virtual host / route configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class HeaderRewriteRule:
    """A single header add/remove/override rule."""
    action: str          # 'add', 'remove', or 'override'
    header: str
    value: Optional[str] = None  # not required for 'remove'

    def to_dict(self) -> Dict:
        d: Dict = {"action": self.action, "header": self.header}
        if self.value is not None:
            d["value"] = self.value
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> "HeaderRewriteRule":
        return cls(
            action=data["action"],
            header=data["header"],
            value=data.get("value"),
        )


@dataclass
class HeaderRewriteValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


_VALID_ACTIONS = {"add", "remove", "override"}


def validate_rule(rule: HeaderRewriteRule) -> HeaderRewriteValidationResult:
    result = HeaderRewriteValidationResult()
    if rule.action not in _VALID_ACTIONS:
        result.errors.append(
            f"Invalid action '{rule.action}'. Must be one of {sorted(_VALID_ACTIONS)}."
        )
    if not rule.header or not rule.header.strip():
        result.errors.append("Header name must not be empty.")
    if rule.action in {"add", "override"} and not rule.value:
        result.errors.append(
            f"Action '{rule.action}' requires a non-empty value."
        )
    if rule.action == "remove" and rule.value is not None:
        result.warnings.append(
            "Value is ignored for 'remove' action."
        )
    return result


def validate_rules(rules: List[HeaderRewriteRule]) -> HeaderRewriteValidationResult:
    combined = HeaderRewriteValidationResult()
    headers_seen: Dict[str, str] = {}
    for rule in rules:
        r = validate_rule(rule)
        combined.errors.extend(r.errors)
        combined.warnings.extend(r.warnings)
        key = rule.header.lower()
        if key in headers_seen:
            combined.warnings.append(
                f"Header '{rule.header}' is targeted by multiple rules "
                f"(actions: '{headers_seen[key]}' and '{rule.action}')."
            )
        else:
            headers_seen[key] = rule.action
    return combined


def rules_to_envoy_headers(rules: List[HeaderRewriteRule]) -> Dict:
    """Convert rules to Envoy route-level request_headers_to_add/remove dicts."""
    to_add = []
    to_remove = []
    for rule in rules:
        if rule.action in {"add", "override"}:
            to_add.append({
                "header": {"key": rule.header, "value": rule.value},
                "keep_empty_value": False,
            })
        elif rule.action == "remove":
            to_remove.append(rule.header)
    result: Dict = {}
    if to_add:
        result["request_headers_to_add"] = to_add
    if to_remove:
        result["request_headers_to_remove"] = to_remove
    return result
