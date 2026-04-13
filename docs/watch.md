# envault watch

The `watch` command monitors a plain-text `.env` file for changes and
automatically re-encrypts it into the vault every time you save the file.

This is useful during active development: edit your `.env` in any editor,
and envault keeps the encrypted vault in sync without any manual `lock` calls.

## Usage

```bash
envault watch .env --vault-dir .envault --password <password>
```

### Options

| Option | Default | Description |
|---|---|---|
| `--vault-dir` | `.envault` | Directory where encrypted vault files are stored. |
| `--password` | _(prompt)_ | Encryption password. |
| `--interval` | `1.0` | Polling interval in seconds. |
| `--backend` | `local` | Storage backend (`local` or `s3`). |

## How it works

1. envault records a SHA-256 hash of the `.env` file at startup.
2. Every `--interval` seconds the hash is recomputed.
3. When the hash changes, `parse_env` + `write_vault` are called, producing a
   new encrypted version in the vault and bumping the version counter.
4. The new version number is printed to stdout.
5. Press **Ctrl-C** to stop watching.

## Example session

```
$ envault watch .env
Password: ****
Watching .env — press Ctrl-C to stop.
  [re-locked] version=2  file=.env
  [re-locked] version=3  file=.env
^CStopped watching.
```

## Notes

- The watcher uses **polling**, not inotify/FSEvents, so it works on all
  platforms including network file systems.
- The `.env` file itself is never deleted or modified by the watcher.
- Combine with `envault push` (or configure a post-lock hook) to
  automatically upload the new version to S3 after each re-lock.
