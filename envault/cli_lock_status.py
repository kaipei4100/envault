"""CLI commands for inspecting and managing vault lock status."""
from __future__ import annotations

import click

from envault.lock_status import (
    get_status,
    set_locked,
    set_unlocked,
    is_locked,
)


@click.group("lock-status", help="Manage per-vault lock status.")
def lock_status_group() -> None:
    pass


@lock_status_group.command("show")
@click.argument("vault")
def status_show(vault: str) -> None:
    """Show the current lock status of VAULT."""
    status = get_status(vault)
    if status["locked"]:
        click.echo(f"Status  : LOCKED")
        click.echo(f"Identity: {status['identity']}")
        click.echo(f"Since   : {status['locked_at']}")
        if status.get("note"):
            click.echo(f"Note    : {status['note']}")
    else:
        click.echo("Status  : unlocked")


@lock_status_group.command("lock")
@click.argument("vault")
@click.option("--identity", "-i", required=True, help="Identity locking the vault.")
@click.option("--note", "-n", default="", help="Optional reason for locking.")
def status_lock(vault: str, identity: str, note: str) -> None:
    """Mark VAULT as locked by IDENTITY."""
    if is_locked(vault):
        current = get_status(vault)
        click.echo(
            f"Already locked by '{current['identity']}' since {current['locked_at']}.",
            err=True,
        )
        raise SystemExit(1)
    result = set_locked(vault, identity, note=note)
    click.echo(f"Vault locked by '{result['identity']}' at {result['locked_at']}.")


@lock_status_group.command("unlock")
@click.argument("vault")
def status_unlock(vault: str) -> None:
    """Remove the lock from VAULT."""
    if not is_locked(vault):
        click.echo("Vault is not locked.")
        return
    set_unlocked(vault)
    click.echo("Vault unlocked.")
