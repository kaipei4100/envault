# Access Control

`envault` supports per-identity permission rules stored alongside the vault in
a `.envault_access.json` file. This lets teams enforce least-privilege access
without relying solely on filesystem permissions.

## Permission Levels

| Level   | Description                              |
|---------|------------------------------------------|
| `read`  | May decrypt and view secrets             |
| `write` | May encrypt and update secrets           |
| `admin` | Full control, including revoking access  |

Levels are ordered: `read` < `write` < `admin`.  
A check for `write` will pass for any identity with `write` **or** `admin`.

## Python API

```python
from pathlib import Path
from envault.access import set_permission, check_permission, WRITE

vault_dir = Path(".envault")

# Grant alice write access
set_permission(vault_dir, "alice", WRITE)

# Enforce before a sensitive operation
try:
    check_permission(vault_dir, "alice", WRITE)
except PermissionError as e:
    print(f"Denied: {e}")
```

## Functions

### `set_permission(vault_dir, identity, level)`
Grant `identity` the given `level`. Overwrites any existing permission.

### `get_permission(vault_dir, identity) -> str | None`
Return the current level for `identity`, or `None` if not configured.

### `revoke_permission(vault_dir, identity)`
Remove `identity` from the access list. Raises `KeyError` if not found.

### `list_permissions(vault_dir) -> list[dict]`
Return all entries sorted by identity name.

### `check_permission(vault_dir, identity, required)`
Raise `PermissionError` if `identity` does not hold at least `required`.

## Storage

Permissions are stored in `<vault_dir>/.envault_access.json`:

```json
{
  "alice": "admin",
  "bob": "read"
}
```

This file should be committed to version control so the whole team shares the
same rules, but **never** contains secrets.
