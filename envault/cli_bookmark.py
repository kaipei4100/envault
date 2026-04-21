"""CLI commands for managing vault bookmarks."""
from __future__ import annotations

import click

from envault.bookmark import (
    BookmarkNotFound,
    delete_bookmark,
    get_bookmark,
    list_bookmarks,
    set_bookmark,
)


@click.group("bookmark", help="Manage human-friendly bookmarks for vault versions.")
def bookmark_group() -> None:  # pragma: no cover
    pass


@bookmark_group.command("set")
@click.argument("vault")
@click.argument("label")
@click.argument("version", type=int)
def bookmark_set(vault: str, label: str, version: int) -> None:
    """Create or overwrite a bookmark LABEL pointing at VERSION."""
    try:
        result = set_bookmark(vault, label, version)
        click.echo(f"Bookmark '{result['label']}' -> v{result['version']} saved.")
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@bookmark_group.command("get")
@click.argument("vault")
@click.argument("label")
def bookmark_get(vault: str, label: str) -> None:
    """Print the version number that LABEL points to."""
    try:
        version = get_bookmark(vault, label)
        click.echo(str(version))
    except BookmarkNotFound as exc:
        raise click.ClickException(str(exc)) from exc


@bookmark_group.command("delete")
@click.argument("vault")
@click.argument("label")
def bookmark_delete(vault: str, label: str) -> None:
    """Remove a bookmark by LABEL."""
    try:
        delete_bookmark(vault, label)
        click.echo(f"Bookmark '{label}' deleted.")
    except BookmarkNotFound as exc:
        raise click.ClickException(str(exc)) from exc


@bookmark_group.command("list")
@click.argument("vault")
def bookmark_list(vault: str) -> None:
    """List all bookmarks for VAULT."""
    entries = list_bookmarks(vault)
    if not entries:
        click.echo("No bookmarks defined.")
        return
    for entry in entries:
        click.echo(f"{entry['label']:30s}  v{entry['version']}")
