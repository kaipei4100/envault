"""CLI commands for managing secret TTLs (time-to-live)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import click

from envault import ttl as ttl_mod


@click.group("ttl")
def ttl_group() -> None:
    """Manage expiry (TTL) for individual secret keys."""


@ttl_group.command("set")
@click.argument("vault_path", type=click.Path(exists=True))
@click.argument("key")
@click.argument("expires_at")  # ISO-8601 string, e.g. 2025-12-31T00:00:00+00:00
def ttl_set(vault_path: str, key: str, expires_at: str) -> None:
    """Set an expiry date for KEY in VAULT_PATH.

    EXPIRES_AT must be an ISO-8601 datetime string, e.g.
    ``2025-12-31T00:00:00+00:00``.
    """
    try:
        dt = datetime.fromisoformat(expires_at)
    except ValueError as exc:
        raise click.BadParameter(str(exc), param_hint="EXPIRES_AT") from exc

    ttl_mod.set_ttl(vault_path, key, dt)
    click.echo(f"TTL set for '{key}': expires {dt.astimezone(timezone.utc).isoformat()}")


@ttl_group.command("get")
@click.argument("vault_path", type=click.Path(exists=True))
@click.argument("key")
def ttl_get(vault_path: str, key: str) -> None:
    """Show the expiry date for KEY, if set."""
    result = ttl_mod.get_ttl(vault_path, key)
    if result is None:
        click.echo(f"No TTL set for '{key}'.")
    else:
        click.echo(result.astimezone(timezone.utc).isoformat())


@ttl_group.command("delete")
@click.argument("vault_path", type=click.Path(exists=True))
@click.argument("key")
def ttl_delete(vault_path: str, key: str) -> None:
    """Remove the TTL for KEY."""
    removed = ttl_mod.delete_ttl(vault_path, key)
    if removed:
        click.echo(f"TTL removed for '{key}'.")
    else:
        click.echo(f"No TTL found for '{key}'.")


@ttl_group.command("list")
@click.argument("vault_path", type=click.Path(exists=True))
def ttl_list(vault_path: str) -> None:
    """List all keys with an expiry date."""
    entries = ttl_mod.list_ttls(vault_path)
    if not entries:
        click.echo("No TTLs configured.")
        return
    for key, expiry in sorted(entries.items()):
        click.echo(f"  {key:<30} {expiry.astimezone(timezone.utc).isoformat()}")


@ttl_group.command("check")
@click.argument("vault_path", type=click.Path(exists=True))
@click.option("--warn-within", default=86_400, show_default=True,
              help="Warn about keys expiring within this many seconds.")
def ttl_check(vault_path: str, warn_within: int) -> None:
    """Report expired or soon-to-expire keys."""
    expired = ttl_mod.expired_keys(vault_path)
    soon = ttl_mod.expiring_soon(vault_path, within_seconds=warn_within)

    if expired:
        click.secho("Expired keys:", fg="red")
        for k in expired:
            click.secho(f"  ✗ {k}", fg="red")

    if soon:
        click.secho("Expiring soon:", fg="yellow")
        for k, expiry in soon:
            click.secho(f"  ⚠ {k}  →  {expiry.astimezone(timezone.utc).isoformat()}", fg="yellow")

    if not expired and not soon:
        click.secho("All secrets are within their TTL.", fg="green")
