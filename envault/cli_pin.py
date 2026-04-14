"""CLI commands for vault pin management."""

from __future__ import annotations

from pathlib import Path

import click

from envault import pin as pin_mod


@click.group("pin")
def pin_group() -> None:
    """Pin a vault to a specific version."""


@pin_group.command("set")
@click.argument("vault_file", type=click.Path(exists=True, path_type=Path))
@click.argument("version", type=int)
@click.option("--note", default="", help="Optional reason for pinning.")
def pin_set(vault_file: Path, version: int, note: str) -> None:
    """Pin VAULT_FILE to VERSION."""
    try:
        pin_mod.set_pin(vault_file, version, note=note)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Pinned {vault_file.name} to version {version}.")


@pin_group.command("show")
@click.argument("vault_file", type=click.Path(exists=True, path_type=Path))
def pin_show(vault_file: Path) -> None:
    """Show the current pin for VAULT_FILE."""
    info = pin_mod.get_pin(vault_file)
    if info is None:
        click.echo("No pin set.")
    else:
        note_part = f"  note: {info['note']}" if info.get("note") else ""
        click.echo(f"Pinned to version {info['version']}.{note_part}")


@pin_group.command("delete")
@click.argument("vault_file", type=click.Path(exists=True, path_type=Path))
def pin_delete(vault_file: Path) -> None:
    """Remove the pin from VAULT_FILE."""
    removed = pin_mod.delete_pin(vault_file)
    if removed:
        click.echo(f"Pin removed from {vault_file.name}.")
    else:
        click.echo("No pin was set.")
