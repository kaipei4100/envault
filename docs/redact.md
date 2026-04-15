# Redaction

The `envault redact` feature lets you safely display or log environment
variables without leaking sensitive values.

## How it works

envault maintains a list of built-in patterns that identify sensitive keys:

| Pattern | Example keys matched |
|---------|----------------------|
| `password` / `passwd` | `DB_PASSWORD`, `PASSWD` |
| `secret` | `SECRET_KEY`, `APP_SECRET` |
| `token` | `ACCESS_TOKEN`, `AUTH_TOKEN` |
| `api_key` / `apikey` / `api-key` | `STRIPE_API_KEY` |
| `private_key` | `PRIVATE_KEY_PEM` |
| `auth` | `AUTH_HEADER` |

Matching is **case-insensitive** and uses substring search, so any key
containing one of the above words will be redacted.

## Masking modes

### Full masking (default)

The entire value is replaced with `*` characters of the same length:

```
DB_PASSWORD=***********
```

### Partial masking (`--partial`)

For values of 8 or more characters, the first two and last two characters
are preserved and the middle is masked:

```
DB_PASSWORD=hu*******r2
```

This is useful for debugging — you can confirm the correct credential is
configured without fully exposing it.

## Extra keys

You can extend the built-in list with project-specific keys:

```bash
envault export shell --redact --redact-key MY_INTERNAL_TOKEN
```

Extra key matching is also case-insensitive.

## Python API

```python
from envault.redact import redact_env, is_sensitive, mask_value

env = {"DB_PASSWORD": "hunter2", "PORT": "5432"}
result = redact_env(env, partial=True)
print(result.redacted)   # {'DB_PASSWORD': 'hu***r2', 'PORT': '5432'}
print(result.redacted_keys)  # ['DB_PASSWORD']
```

### `is_sensitive(key) -> bool`

Returns `True` if the key matches any sensitive pattern.

### `mask_value(value, partial=False) -> str`

Returns a masked version of the value.

### `redact_env(env, extra_keys=None, partial=False) -> RedactResult`

Redacts all sensitive values in the mapping and returns a `RedactResult`
with `.original`, `.redacted`, and `.redacted_keys` attributes.
