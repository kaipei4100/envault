# Policy Enforcement

envault supports per-vault **policies** that restrict which operations are allowed,
enforce note requirements, and set password complexity rules.

## Policy File

A policy is stored as `.envault-policy.json` inside the vault directory.
If no file is present, permissive defaults are used.

```json
{
  "allowed_operations": ["lock", "unlock", "push", "pull", "rotate", "import", "export"],
  "require_note": false,
  "min_password_length": 8,
  "max_versions": null,
  "read_only": false
}
```

## Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `allowed_operations` | list | all ops | Whitelist of permitted operations. |
| `require_note` | bool | `false` | If `true`, every mutating operation must include a `--note`. |
| `min_password_length` | int | `8` | Minimum characters required in any password. |
| `max_versions` | int\|null | `null` | Cap on stored versions (null = unlimited). |
| `read_only` | bool | `false` | When `true`, only `unlock`, `pull`, and `export` are permitted. |

## Example: Enforce Notes and Strong Passwords

```json
{
  "require_note": true,
  "min_password_length": 20
}
```

With this policy any `lock`, `rotate`, or `push` without `--note` will be
rejected before touching the vault.

## Read-Only Vaults

Set `"read_only": true` to prevent any writes to the vault.
Useful for production environments where secrets should only be consumed,
never modified through the CLI.

## Programmatic Usage

```python
from pathlib import Path
from envault.policy import load_policy, check_operation

policy = load_policy(Path(".envault"))
violation = check_operation(policy, "push", note="deploy v2", password="s3cr3tpassword")
if violation:
    raise SystemExit(str(violation))
```
