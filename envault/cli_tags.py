"""CLI commands for managing vault version tags."""

from __future__ import annotations

from pathlib import Path

import click

from envault.tags import (
    set_tag,
    delete_tag,
    resolve_tag,
    list_tags,
    find_tags_for_version,
)


@click.group("tag")
def tag_group() -> None:
    """Manage named tags for vault versions."""


@tag_group.command("set")
@click.argument("tag")
@click.argument("version", type=int)
@click.option("--vault-dir", default=".", show_default=True, help="Path to vault directory.")
def tag_set(tag: str, version: int, vault_dir: str) -> None:
    """Attach TAG to a specific VERSION number."""
    d = Path(vault_dir)
    try:
        set_tag(d, tag, version)
        click.echo(f"Tag '{tag}' -> version {version}")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@tag_group.command("get")
@click.argument("tag")
@click.option("--vault-dir", default=".", show_default=True)
def tag_get(tag: str, vault_dir: str) -> None:
    """Print the version number that TAG points to."""
    d = Path(vault_dir)
    try:
        version = resolve_tag(d, tag)
        click.echo(str(version))
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc


@tag_group.command("delete")
@click.argument("tag")
@click.option("--vault-dir", default=".", show_default=True)
def tag_delete(tag: str, vault_dir: str) -> None:
    """Remove TAG from the vault."""
    d = Path(vault_dir)
    try:
        delete_tag(d, tag)
        click.echo(f"Tag '{tag}' deleted.")
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc


@tag_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
def tag_list(vault_dir: str) -> None:
    """List all tags and the versions they point to."""
    entries = list_tags(Path(vault_dir))
    if not entries:
        click.echo("No tags defined.")
        return
    for entry in entries:
        click.echo(f"{entry['tag']:20s}  ->  v{entry['version']}")


@tag_group.command("find")
@click.argument("version", type=int)
@click.option("--vault-dir", default=".", show_default=True)
def tag_find(version: int, vault_dir: str) -> None:
    """Find all tags pointing to VERSION."""
    tags = find_tags_for_version(Path(vault_dir), version)
    if not tags:
        click.echo(f"No tags point to version {version}.")
    else:
        click.echo("  ".join(tags))
