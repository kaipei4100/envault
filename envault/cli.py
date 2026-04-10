"""Command-line interface for envault.

Provides commands for encrypting, decrypting, pushing, pulling,
and inspecting versioned .env files.
"""

import sys
import os
import getpass
import json
from pathlib import Path

import click

from envault.crypto import encrypt, decrypt, fingerprint
from envault.vault import write_vault, read_vault, vault_metadata, _next_version
from envault.parser import parse_env, serialise_env, diff_envs
from envault.backends import LocalBackend, S3Backend


DEFAULT_ENV_FILE = ".env"
DEFAULT_VAULT_FILE = ".env.vault"


def _get_backend(ctx_obj: dict):
    """Instantiate the appropriate backend from CLI context."""
    backend_type = ctx_obj.get("backend", "local")
    if backend_type == "s3":
        bucket = ctx_obj.get("bucket")
        prefix = ctx_obj.get("prefix", "envault/")
        if not bucket:
            raise click.UsageError("--bucket is required when using the s3 backend.")
        return S3Backend(bucket=bucket, prefix=prefix)
    # Default: local
    store_dir = ctx_obj.get("store", ".envault-store")
    return LocalBackend(store_dir=store_dir)


@click.group()
@click.option("--backend", default="local", type=click.Choice(["local", "s3"]),
              show_default=True, help="Storage backend to use.")
@click.option("--store", default=".envault-store", show_default=True,
              help="Directory for the local backend.")
@click.option("--bucket", default=None, help="S3 bucket name (s3 backend only).")
@click.option("--prefix", default="envault/", show_default=True,
              help="Key prefix inside the S3 bucket.")
@click.pass_context
def cli(ctx, backend, store, bucket, prefix):
    """envault — encrypt and version your .env files."""
    ctx.ensure_object(dict)
    ctx.obj["backend"] = backend
    ctx.obj["store"] = store
    ctx.obj["bucket"] = bucket
    ctx.obj["prefix"] = prefix


@cli.command("lock")
@click.argument("env_file", default=DEFAULT_ENV_FILE, type=click.Path(exists=True))
@click.option("--out", default=DEFAULT_VAULT_FILE, show_default=True,
              help="Output vault file path.")
@click.option("--password", envvar="ENVAULT_PASSWORD", default=None,
              help="Encryption password (prompted if omitted).")
@click.pass_context
def lock(ctx, env_file, out, password):
    """Encrypt ENV_FILE and write a versioned vault file."""
    if password is None:
        password = getpass.getpass("Encryption password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            raise click.ClickException("Passwords do not match.")

    plaintext = Path(env_file).read_bytes()
    ciphertext = encrypt(plaintext, password)
    write_vault(Path(out), ciphertext)
    fp = fingerprint(plaintext)
    click.echo(f"Locked {env_file} → {out}  (fingerprint: {fp})")


@cli.command("unlock")
@click.argument("vault_file", default=DEFAULT_VAULT_FILE, type=click.Path(exists=True))
@click.option("--out", default=DEFAULT_ENV_FILE, show_default=True,
              help="Output .env file path.")
@click.option("--password", envvar="ENVAULT_PASSWORD", default=None,
              help="Decryption password (prompted if omitted).")
@click.pass_context
def unlock(ctx, vault_file, out, password):
    """Decrypt VAULT_FILE and write a plain .env file."""
    if password is None:
        password = getpass.getpass("Decryption password: ")

    ciphertext = read_vault(Path(vault_file))
    try:
        plaintext = decrypt(ciphertext, password)
    except Exception:
        raise click.ClickException("Decryption failed — wrong password or corrupted vault.")

    Path(out).write_bytes(plaintext)
    fp = fingerprint(plaintext)
    click.echo(f"Unlocked {vault_file} → {out}  (fingerprint: {fp})")


@cli.command("push")
@click.argument("vault_file", default=DEFAULT_VAULT_FILE, type=click.Path(exists=True))
@click.pass_context
def push(ctx, vault_file):
    """Upload VAULT_FILE to the configured backend."""
    backend = _get_backend(ctx.obj)
    meta = vault_metadata(Path(vault_file))
    key = f"v{meta['version']}/{Path(vault_file).name}"
    backend.upload(local_path=Path(vault_file), key=key)
    click.echo(f"Pushed {vault_file} as {key}")


@cli.command("pull")
@click.option("--version", "ver", default=None, type=int,
              help="Version to pull (defaults to latest).")
@click.option("--out", default=DEFAULT_VAULT_FILE, show_default=True,
              help="Destination vault file path.")
@click.pass_context
def pull(ctx, ver, out):
    """Download a vault file from the configured backend."""
    backend = _get_backend(ctx.obj)
    vault_name = Path(out).name

    if ver is None:
        # List available keys and pick the highest version number
        keys = backend.list_keys(prefix="v")
        matching = [k for k in keys if k.endswith(vault_name)]
        if not matching:
            raise click.ClickException("No vault files found in the backend.")
        # Sort by version number embedded in path (v<N>/...)
        def _ver(k):
            try:
                return int(k.split("/")[0].lstrip("v"))
            except (IndexError, ValueError):
                return 0
        key = sorted(matching, key=_ver)[-1]
    else:
        key = f"v{ver}/{vault_name}"
        if not backend.exists(key):
            raise click.ClickException(f"Version {ver} not found in the backend.")

    backend.download(key=key, local_path=Path(out))
    click.echo(f"Pulled {key} → {out}")


@cli.command("diff")
@click.argument("file_a", type=click.Path(exists=True))
@click.argument("file_b", type=click.Path(exists=True))
def diff(file_a, file_b):
    """Show differences between two plain .env files."""
    env_a = parse_env(Path(file_a).read_text())
    env_b = parse_env(Path(file_b).read_text())
    changes = diff_envs(env_a, env_b)
    if not changes:
        click.echo("No differences found.")
        return
    for key, (old, new) in changes.items():
        if old is None:
            click.echo(click.style(f"+ {key}={new}", fg="green"))
        elif new is None:
            click.echo(click.style(f"- {key}={old}", fg="red"))
        else:
            click.echo(click.style(f"~ {key}: {old!r} → {new!r}", fg="yellow"))


@cli.command("info")
@click.argument("vault_file", default=DEFAULT_VAULT_FILE, type=click.Path(exists=True))
def info(vault_file):
    """Display metadata for VAULT_FILE."""
    meta = vault_metadata(Path(vault_file))
    click.echo(json.dumps(meta, indent=2, default=str))


def main():
    """Entry point used by the installed console script."""
    cli(obj={})


if __name__ == "__main__":
    main()
