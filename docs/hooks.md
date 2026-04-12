# Hooks

envault supports lightweight shell hooks that fire before or after key operations.

## Supported Events

| Event | Fires |
|---|---|
| `pre-lock` | Before encrypting a `.env` file |
| `post-lock` | After encrypting a `.env` file |
| `pre-unlock` | Before decrypting a vault |
| `post-unlock` | After decrypting a vault |
| `pre-push` | Before pushing to a backend |
| `post-push` | After pushing to a backend |
| `post-pull` | After pulling from a backend |

## Configuration

Hooks are stored in `.envault-hooks` at the root of your vault directory:

```
# .envault-hooks
post-lock=git add .env.vault && git commit -m "chore: update vault"
pre-push=make test
post-pull=echo "Vault updated from remote"
```

## CLI Usage

### Set a hook

```bash
envault hook set post-lock "git add .env.vault"
```

### Remove a hook

```bash
envault hook unset post-lock
```

### List all hooks

```bash
envault hook list
```

## Environment Variables

Hooks inherit the current shell environment. envault may inject additional
variables (e.g. `ENVAULT_VERSION`, `ENVAULT_EVENT`) in future releases.

## Exit Codes

If a **pre-** hook exits with a non-zero code, the operation is aborted.
Post-hooks are informational and do not affect the outcome.
