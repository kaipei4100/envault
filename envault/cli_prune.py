"""CLI commands for snapshot pruning."""
from __future__ import annotations

from pathlib import Path

import click

from envault.prune import get_prune_policy, prune, set_prune_policy


@click.group("prune")
def prune_group() -> None:
    """Manage automatic pruning of old snapshots."""


@prune_group.command("run")
@click.argument("vault", type=click.Path(exists=True, dir_okay=False))
@click.option("--keep", default=None, type=int, help="Number of snapshots to keep.")
def prune_run(vault: str, keep: int | None) -> None:
    """Prune snapshots for VAULT, keeping the N most recent.

    If --keep is omitted the stored policy is used.  Exits with an
    error when no keep value can be determined.
    """
    vault_path = Path(vault)

    if keep is None:
        policy = get_prune_policy(vault_path)
        if policy is None:
            raise click.ClickException(
                "No prune policy set. Pass --keep or run 'envault prune policy'."
            )
        keep = policy["keep"]

    result = prune(vault_path, keep)
    click.echo(result.summary())
    if result.removed:
        click.echo("Removed versions: " + ", ".join(str(v) for v in result.removed))


@prune_group.command("policy")
@click.argument("vault", type=click.Path(exists=True, dir_okay=False))
@click.option("--keep", required=True, type=int, help="Snapshots to retain.")
def prune_policy(vault: str, keep: int) -> None:
    """Set the default prune policy (keep N snapshots) for VAULT."""
    vault_path = Path(vault)
    cfg = set_prune_policy(vault_path, keep)
    click.echo(f"Prune policy set: keep={cfg['keep']}")


@prune_group.command("show")
@click.argument("vault", type=click.Path(exists=True, dir_okay=False))
def prune_show(vault: str) -> None:
    """Show the current prune policy for VAULT."""
    vault_path = Path(vault)
    policy = get_prune_policy(vault_path)
    if policy is None:
        click.echo("No prune policy configured.")
    else:
        click.echo(f"keep={policy['keep']}")
