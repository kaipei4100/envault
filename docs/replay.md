# Replay

The **replay** feature lets you restore a vault to any previously snapshotted
version. This is useful when a bad value was committed and you need to roll back
quickly without manually editing files.

## How it works

1. Every time a snapshot is saved (via `envault snapshot save`), the encrypted
   state of the vault is persisted alongside the audit log entry for that
   version.
2. `replay_to_version` decrypts the target snapshot using the current password
   and writes a **new** vault version containing the historical data. The
   history is never rewritten — the rollback itself becomes a new entry.

## API

```python
from envault.replay import list_replayable, replay_to_version

# See which versions can be replayed
entries = list_replayable(vault_path)
for e in entries:
    print(e["version"], e["action"], e.get("note", ""))

# Restore version 3
event = replay_to_version(vault_path, target_version=3, password="s3cr3t",
                           note="rolling back bad deploy")
print(event)
```

## Errors

| Exception | Cause |
|-----------|-------|
| `ReplayError` | No snapshot exists for the requested version |
| `crypto.DecryptionError` | Wrong password supplied |

## Notes

- Only versions that have a corresponding snapshot file are replayable.
  Use `envault snapshot list` to see available snapshots.
- The replay operation respects any active **policy** restrictions on the
  `replay` action.
- After a successful replay the audit log will contain an entry with
  `action = "replay"` and a `replayed_from` field pointing to the source
  version.
