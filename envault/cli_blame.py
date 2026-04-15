"""cli_blame.py – CLI surface for `envault blame`."""

from pathlib import Path

import click

from envault.blame import blame, format_blame


@click.group("blame")
def blame_group() -> None:
    """Show which version last changed each key."""


@blame_group.command("run")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.option("--password", "-p", envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
@click.option("--show-values", is_flag=True, default=False, help="Include decrypted values.")
@click.option("--key", "-k", default=None, help="Filter output to a single key.")
def blame_run(
    vault: Path,
    password: str,
    show_values: bool,
    key: str | None,
) -> None:
    """Print a blame table for every key in VAULT."""
    try:
        lines = blame(vault, password)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if key:
        lines = [bl for bl in lines if bl.key == key]
        if not lines:
            raise click.ClickException(f"Key {key!r} not found in blame history.")

    click.echo(format_blame(lines, show_values=show_values))
