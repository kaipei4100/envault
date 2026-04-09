# envault

> A CLI tool for encrypting and versioning `.env` files with team-sharing support via S3 or local backends.

---

## Installation

```bash
pip install envault
```

Or with optional S3 support:

```bash
pip install envault[s3]
```

---

## Usage

Initialize envault in your project:

```bash
envault init
```

Encrypt and push your `.env` file:

```bash
envault push --env .env --backend s3 --bucket my-team-bucket
```

Pull and decrypt the latest version:

```bash
envault pull --backend s3 --bucket my-team-bucket
```

List available versions:

```bash
envault versions
```

Restore a specific version:

```bash
envault restore --version 3
```

### Local Backend Example

```bash
envault push --env .env --backend local --path ./vault
envault pull --backend local --path ./vault
```

---

## Backends

| Backend | Description              |
|---------|--------------------------|
| `local` | Store versions on disk   |
| `s3`    | Share with team via AWS S3 |

---

## License

This project is licensed under the [MIT License](LICENSE).