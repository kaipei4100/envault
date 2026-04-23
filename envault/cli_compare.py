"""CLI sub-command: envault compare."""
from __future__ import annotations

import click

from envault.compare import compare_versions, format_compare


@click.group("compare")
def compare_group() -> None:
    """Compare two versions of a vault."""


@compare_group.command("run")
@click.argument("vault_path")
@click.argument("version_a", type=int)
@click.argument("version_b", type=int)
@click.option(
    "--password",
    envvar="ENVAULT_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Decryption password.",
)
@click.option(
    "--show-unchanged",
    is_flag=True,
    default=False,
    help="Also display keys that did not change.",
)
def compare_run(
    vault_path: str,
    version_a: int,
    version_b: int,
    password: str,
    show_unchanged: bool,
) -> None:
    """Compare VERSION_A and VERSION_B of VAULT_PATH."""
    try:
        result = compare_versions(vault_path, password, version_a, version_b)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    click.echo(format_compare(result, show_unchanged=show_unchanged))

    summary_parts = []
    if result.added:
        summary_parts.append(f"{len(result.added)} added")
    if result.removed:
        summary_parts.append(f"{len(result.removed)} removed")
    if result.changed:
        summary_parts.append(f"{len(result.changed)} changed")

    if summary_parts:
        click.echo("Summary: " + ", ".join(summary_parts))
    else:
        click.echo("Versions are identical.")
