"""Policy enforcement for vault access and operations."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

POLICY_FILE = ".envault-policy.json"

ALLOWED_EVENTS = {"lock", "unlock", "push", "pull", "rotate", "import", "export"}


@dataclass
class Policy:
    allowed_operations: List[str] = field(default_factory=lambda: list(ALLOWED_EVENTS))
    require_note: bool = False
    min_password_length: int = 8
    max_versions: Optional[int] = None
    read_only: bool = False


def _policy_path(vault_dir: Path) -> Path:
    return vault_dir / POLICY_FILE


def load_policy(vault_dir: Path) -> Policy:
    """Load policy from vault directory; return defaults if missing."""
    path = _policy_path(vault_dir)
    if not path.exists():
        return Policy()
    data = json.loads(path.read_text())
    return Policy(
        allowed_operations=data.get("allowed_operations", list(ALLOWED_EVENTS)),
        require_note=data.get("require_note", False),
        min_password_length=data.get("min_password_length", 8),
        max_versions=data.get("max_versions"),
        read_only=data.get("read_only", False),
    )


def save_policy(vault_dir: Path, policy: Policy) -> None:
    """Persist policy to vault directory."""
    vault_dir.mkdir(parents=True, exist_ok=True)
    _policy_path(vault_dir).write_text(
        json.dumps(
            {
                "allowed_operations": policy.allowed_operations,
                "require_note": policy.require_note,
                "min_password_length": policy.min_password_length,
                "max_versions": policy.max_versions,
                "read_only": policy.read_only,
            },
            indent=2,
        )
    )


@dataclass
class PolicyViolation:
    message: str

    def __str__(self) -> str:
        return self.message


def check_operation(policy: Policy, operation: str, note: Optional[str] = None, password: Optional[str] = None) -> Optional[PolicyViolation]:
    """Return a PolicyViolation if the operation is not allowed, else None."""
    if policy.read_only and operation not in ("unlock", "pull", "export"):
        return PolicyViolation(f"Vault is read-only; operation '{operation}' is not permitted.")
    if operation not in policy.allowed_operations:
        return PolicyViolation(f"Operation '{operation}' is not allowed by policy.")
    if policy.require_note and not note:
        return PolicyViolation("A note is required for this operation by policy.")
    if password is not None and len(password) < policy.min_password_length:
        return PolicyViolation(
            f"Password must be at least {policy.min_password_length} characters."
        )
    return None
