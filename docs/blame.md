# envault blame

The `blame` feature lets you trace **which version** (and which audit event) last
changed every key in a vault — similar to `git blame` but for encrypted `.env`
files.

## Usage

```bash
envault blame run path/to/secrets.vault --password $PASS
```

Sample output:

```
ver   timestamp                  user                 key
------------------------------------------------------------
v1    2024-05-01T10:00:00+00:00  alice@example.com    DEBUG
v2    2024-05-03T14:22:11+00:00  bob@example.com      HOST
v1    2024-05-01T10:00:00+00:00  alice@example.com    PORT
```

### Options

| Flag | Description |
|------|-------------|
| `--password / -p` | Decryption password (or set `ENVAULT_PASSWORD`). |
| `--show-values` | Include the decrypted value in the output. |
| `--key / -k KEY` | Restrict output to a single key. |

## How it works

1. All audit events stored alongside the vault are read and sorted by version.
2. For each version, the vault is decrypted and parsed.
3. A key is attributed to the **oldest version** where it first appeared with
   its current value.  If a later version changed the value, attribution moves
   to that version.
4. Keys that were removed in a later version are omitted from the output.

## Python API

```python
from envault.blame import blame, format_blame

lines = blame(Path("secrets.vault"), password="s3cr3t")
print(format_blame(lines, show_values=False))
```

Each element in the returned list is a `BlameLine` dataclass:

```python
@dataclass
class BlameLine:
    key: str
    value: str
    version: int
    event: str
    user: Optional[str]
    note: Optional[str]
    timestamp: Optional[str]
```
