# Export

The `export` command decrypts a vault file and renders its contents in a
choice of formats, making it easy to source variables into a shell session,
pass them to Docker, or feed them into other tooling.

## Usage

```
envault export print [OPTIONS] VAULT_PATH
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--format` / `-f` | `shell` | Output format: `shell`, `docker`, or `json` |
| `--no-export` | off | Omit the `export` keyword (shell format only) |
| `--output` / `-o` | stdout | Write output to a file instead of stdout |
| `--password` / `-p` | prompted | Vault decryption password |

## Formats

### shell (default)

Emits POSIX-compatible `export KEY='value'` statements, sorted by key.
Values are shell-quoted so that spaces and special characters are safe.

```bash
envault export print prod.vault --format shell > /tmp/env.sh
source /tmp/env.sh
```

Use `--no-export` to get plain `KEY=value` lines suitable for `.env` loaders:

```bash
envault export print prod.vault --no-export
```

### docker

Emits `--env KEY='value'` pairs that can be embedded in a `docker run` call:

```bash
docker run $(envault export print prod.vault --format docker) myimage
```

### json

Emits a pretty-printed JSON object — useful for piping into `jq` or other
tools:

```bash
envault export print prod.vault --format json | jq '.DATABASE_URL'
```

## Security note

Decrypted values are written to stdout (or a file) in **plain text**.
Avoid redirecting output to world-readable locations and prefer ephemeral
files or process-substitution where possible.
