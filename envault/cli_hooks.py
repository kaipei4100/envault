"""CLI commands for managing envault hooks."""

from __future__ import annotations

import click
from pathlib import Path

from envault.hooks import load_hooks, save_hooks, _VALID_EVENTS


@click.group(name="hook")
def hook_group() -> None:
    """Manage pre/post operation hooks."""


@hook_group.command("set")
@click.argument("event", metavar="EVENT")
@click.argument("command", metavar="COMMAND")
@click.option("--vault-dir", default=".", show_default=True)
def hook_set(event: str, command: str, vault_dir: str) -> None:
    """Set a hook COMMAND for EVENT.

    Valid events: pre-lock, post-lock, pre-unlock, post-unlock,
    pre-push, post-push, post-pull.
    """
    if event not in _VALID_EVENTS:
        raise click.BadParameter(
            f"Unknown event {event!r}. Valid: {', '.join(sorted(_VALID_EVENTS))}",
            param_hint="EVENT",
        )
    path = Path(vault_dir)
    hooks = load_hooks(path)
    hooks[event] = command
    save_hooks(path, hooks)
    click.echo(f"Hook set: {event} → {command}")


@hook_group.command("unset")
@click.argument("event", metavar="EVENT")
@click.option("--vault-dir", default=".", show_default=True)
def hook_unset(event: str, vault_dir: str) -> None:
    """Remove the hook for EVENT."""
    path = Path(vault_dir)
    hooks = load_hooks(path)
    if event not in hooks:
        click.echo(f"No hook defined for {event!r}.")
        return
    del hooks[event]
    save_hooks(path, hooks)
    click.echo(f"Hook removed: {event}")


@hook_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
def hook_list(vault_dir: str) -> None:
    """List all configured hooks."""
    hooks = load_hooks(Path(vault_dir))
    if not hooks:
        click.echo("No hooks configured.")
        return
    for event, command in sorted(hooks.items()):
        click.echo(f"  {event:<16} {command}")
