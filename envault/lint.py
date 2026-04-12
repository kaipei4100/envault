"""Lint .env files for common issues before encrypting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LintIssue:
    line: int
    key: str | None
    code: str
    message: str
    severity: str  # "error" | "warning"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def lint_env(pairs: Dict[str, str], raw_lines: List[str] | None = None) -> LintResult:
    """Run all lint checks and return a LintResult."""
    result = LintResult()
    result.issues.extend(_check_empty_values(pairs))
    result.issues.extend(_check_duplicate_keys(raw_lines or []))
    result.issues.extend(_check_key_naming(pairs))
    result.issues.extend(_check_whitespace_values(pairs))
    return result


def _check_empty_values(pairs: Dict[str, str]) -> List[LintIssue]:
    issues = []
    for key, value in pairs.items():
        if value == "":
            issues.append(LintIssue(
                line=0, key=key, code="W001",
                message=f"{key} has an empty value.",
                severity="warning",
            ))
    return issues


def _check_duplicate_keys(raw_lines: List[str]) -> List[LintIssue]:
    seen: Dict[str, int] = {}
    issues = []
    for lineno, line in enumerate(raw_lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in seen:
                issues.append(LintIssue(
                    line=lineno, key=key, code="E001",
                    message=f"{key} is defined more than once (first at line {seen[key]}).",
                    severity="error",
                ))
            else:
                seen[key] = lineno
    return issues


def _check_key_naming(pairs: Dict[str, str]) -> List[LintIssue]:
    import re
    issues = []
    pattern = re.compile(r'^[A-Z][A-Z0-9_]*$')
    for key in pairs:
        if not pattern.match(key):
            issues.append(LintIssue(
                line=0, key=key, code="W002",
                message=f"{key} does not follow UPPER_SNAKE_CASE convention.",
                severity="warning",
            ))
    return issues


def _check_whitespace_values(pairs: Dict[str, str]) -> List[LintIssue]:
    issues = []
    for key, value in pairs.items():
        if value != value.strip():
            issues.append(LintIssue(
                line=0, key=key, code="W003",
                message=f"{key} value has leading or trailing whitespace.",
                severity="warning",
            ))
    return issues


def format_lint_results(result: LintResult) -> str:
    if not result.issues:
        return "No issues found."
    lines = []
    for issue in result.issues:
        loc = f"line {issue.line}" if issue.line else "—"
        lines.append(f"[{issue.severity.upper()}] {issue.code} ({loc}): {issue.message}")
    return "\n".join(lines)
