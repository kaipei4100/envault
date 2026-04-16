# Vault Quota

envault can enforce a byte-size quota on vault storage to prevent unbounded growth, particularly useful when using local backends with limited disk space.

## Setting a Quota

```bash
envault quota set --vault secrets.vault --max-bytes 1048576
```

This stores the limit alongside the vault. The quota applies to all non-hidden files in the vault's directory.

## Checking Usage

```bash
envault quota check --vault secrets.vault
```

Outputs current usage and whether the quota has been exceeded:

```
Used:  204,800 bytes
Limit: 1,048,576 bytes
Status: OK
```

## Removing a Quota

```bash
envault quota delete --vault secrets.vault
```

## Python API

```python
from pathlib import Path
from envault.quota import set_quota, check_quota, QuotaExceeded

vault = Path("secrets.vault")

# Configure a 1 MB quota
set_quota(vault, max_bytes=1_048_576)

# Check before writing
try:
    check_quota(vault)
except QuotaExceeded as e:
    print(f"Cannot write: {e}")
```

## Functions

| Function | Description |
|---|---|
| `set_quota(vault_path, max_bytes)` | Set quota limit in bytes |
| `get_quota(vault_path)` | Return current limit or `None` |
| `delete_quota(vault_path)` | Remove quota configuration |
| `current_usage(vault_path)` | Measure bytes used on disk |
| `check_quota(vault_path)` | Raise `QuotaExceeded` if over limit |

## Notes

- Quota files are stored as `.quota.json` and are excluded from usage calculations.
- `check_quota` is a read-only operation; it does not block writes automatically. Integrate it into your workflow or CI pipeline.
