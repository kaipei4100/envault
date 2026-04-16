# Archive

The `archive` feature lets you compress old vault snapshots into a zip bundle,
keeping your snapshot directory lean while retaining full history.

## Commands

### `envault archive create <vault>`

Moves old snapshots into a `.archive.zip` file next to the vault, keeping the
N most recent snapshots in place.

```bash
envault archive create myapp.vault --keep 3
# Archived versions: [1, 2]
# Archive: myapp.archive.zip (4096 bytes)
```

Options:
- `--password` — vault password (prompted if omitted)
- `--keep` — number of recent snapshots to leave on disk (default: 3)

### `envault archive list <vault>`

Lists version numbers currently stored inside the archive.

```bash
envault archive list myapp.vault
  v1
  v2
```

### `envault archive restore <vault> <version>`

Extracts a single version from the archive back into the snapshot directory so
that other commands (e.g. `replay`, `snapshot`) can access it again.

```bash
envault archive restore myapp.vault 1
# Restored v1 to .envault-snapshots/v1.enc
```

## How it works

1. `create_archive` reads the snapshot list via `list_snapshots`.
2. All but the `--keep` most recent entries are written into a `zipfile.ZipFile`
   with `ZIP_DEFLATED` compression.
3. The original `.enc` files are deleted after being written to the archive.
4. The archive is opened in append mode (`"a"`), so repeated calls accumulate
   older snapshots without overwriting existing ones.

## Notes

- The archive is **not** encrypted beyond what the individual `.enc` snapshot
  files already provide (each snapshot is AES-encrypted with your password).
- To fully restore a historical version, use `archive restore` followed by
  `envault replay`.
