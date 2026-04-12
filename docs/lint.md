# envault lint

The `lint` command inspects a `.env` file for common issues **before** it is
encrypted and stored. Catching problems early prevents bad data from being
shared with the team.

## Usage

```bash
envault lint [OPTIONS] [ENV_FILE]
```

| Option | Default | Description |
|---|---|---|
| `--strict` | off | Exit with a non-zero code on warnings as well as errors |
| `--json` | off | Output results as JSON |

## Checks

### E001 — Duplicate key

A key appears more than once in the file. The **last** value wins at runtime,
but the duplication is almost always a mistake.

```
[ERROR] E001 (line 12): DATABASE_URL is defined more than once (first at line 3).
```

### W001 — Empty value

A key is present but has no value assigned. This may be intentional (opt-in
placeholder) but is flagged as a warning so it is not overlooked.

```
[WARNING] W001 (—): STRIPE_SECRET_KEY has an empty value.
```

### W002 — Key naming convention

envault encourages `UPPER_SNAKE_CASE` for all keys. Mixed-case or camelCase
keys trigger this warning.

```
[WARNING] W002 (—): myApiKey does not follow UPPER_SNAKE_CASE convention.
```

### W003 — Whitespace in value

Leading or trailing whitespace inside a value is stripped by some loaders and
preserved by others, causing subtle cross-platform bugs.

```
[WARNING] W003 (—): SECRET_KEY value has leading or trailing whitespace.
```

## Exit codes

| Code | Meaning |
|---|---|
| `0` | No errors (warnings may be present) |
| `1` | One or more **errors** found |
| `2` | `--strict` mode and one or more **warnings** found |

## Integration with `lock`

Passing `--lint` to `envault lock` runs the linter automatically before
encrypting. The lock is aborted if any errors are detected.

```bash
envault lock --lint secrets.env
```
