"""CLI commands for vault archiving."""
from __future__ import annotations

import click
from pathlib import Path

from envault.archive import create_archive, list_archived, restore_from_archive


@click.group("archive")
def archive_group() -> None:
    """Manage vault snapshot archives."""


@archive_group.command("create")
@click.argument("vault", type=click.Path(exists=True))
@click.option("--password", prompt=True, hide_input=True)
@click.option("--keep", default=3, show_default=True, help="Number of recent snapshots to keep.")
def archive_create(vault: str, password: str, keep: int) -> None:
    """Archive old snapshots, keeping the N most recent."""
    if keep < 1:
        raise click.BadParameter("Must keep at least 1 snapshot.", param_hint="'--keep'")
    result = create_archive(Path(vault), password, keep_latest=keep)
    if not result.versions:
        click.echo("Nothing to archive.")
        return
    click.echo(f"Archived versions: {result.versions}")
    click.echo(f"Archive: {result.path} ({result.size_bytes} bytes)")


@archive_group.command("list")
@click.argument("vault", type=click.Path(exists=True))
def archive_list(vault: str) -> None:
    """List versions stored in the archive."""
    versions = list_archived(Path(vault))
    if not versions:
        click.echo("Archive is empty or does not exist.")
        return
    for v in versions:
        click.echo(f"  v{v}")


@archive_group.command("restore")
@click.argument("vault", type=click.Path(exists=True))
@click.argument("version", type=int)
def archive_restore(vault: str, version: int) -> None:
    """Restore a specific version from the archive."""
    try:
        path = restore_from_archive(Path(vault), version)
        click.echo(f"Restored v{version} to {path}")
    except (FileNotFoundError, KeyError) as exc:
        raise click.ClickException(str(exc))
