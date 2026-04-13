"""CLI commands for vault checksum management."""

from __future__ import annotations

from pathlib import Path

import click

from envault.checksum import (
    ChecksumMismatch,
    checksum_exists,
    compute,
    save_checksum,
    verify_checksum,
)


@click.group("checksum")
def checksum_group() -> None:
    """Manage vault file checksums."""


@checksum_group.command("generate")
@click.argument("vault_path", type=click.Path(exists=True, path_type=Path))
def checksum_generate(vault_path: Path) -> None:
    """Generate and save a checksum for VAULT_PATH."""
    data = vault_path.read_bytes()
    out = save_checksum(vault_path, data)
    digest = compute(data)
    click.echo(f"Checksum saved: {out}")
    click.echo(f"  sha256: {digest}")


@checksum_group.command("verify")
@click.argument("vault_path", type=click.Path(exists=True, path_type=Path))
def checksum_verify(vault_path: Path) -> None:
    """Verify the integrity of VAULT_PATH against its stored checksum."""
    if not checksum_exists(vault_path):
        click.echo(
            click.style(f"No checksum file found for {vault_path.name}.", fg="yellow")
        )
        raise SystemExit(1)

    try:
        digest = verify_checksum(vault_path)
        click.echo(click.style(f"OK  {vault_path.name}", fg="green"))
        click.echo(f"  sha256: {digest}")
    except ChecksumMismatch as exc:
        click.echo(click.style(f"FAIL  {exc}", fg="red"), err=True)
        raise SystemExit(1)


@checksum_group.command("show")
@click.argument("vault_path", type=click.Path(exists=True, path_type=Path))
def checksum_show(vault_path: Path) -> None:
    """Show the stored checksum for VAULT_PATH without verifying."""
    from envault.checksum import _checksum_path
    import json

    cp = _checksum_path(vault_path)
    if not cp.exists():
        click.echo(f"No checksum file for {vault_path.name}.")
        raise SystemExit(1)

    record = json.loads(cp.read_text())
    click.echo(f"vault    : {record.get('vault')}")
    click.echo(f"algorithm: {record.get('algorithm')}")
    click.echo(f"digest   : {record.get('digest')}")
