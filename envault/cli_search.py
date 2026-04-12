"""CLI commands for searching keys/values inside a vault."""

from __future__ import annotations

import click

from envault.cli import _get_backend
from envault.crypto import decrypt
from envault.parser import parse_env
from envault.search import format_results, search_all, search_keys, search_values
from envault.vault import read_vault


@click.group("search")
def search_group() -> None:
    """Search keys and values inside an encrypted vault."""


@search_group.command("run")
@click.argument("pattern")
@click.option("--vault", "vault_path", required=True, help="Path to .vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option(
    "--target",
    type=click.Choice(["keys", "values", "all"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Which part of each entry to match against.",
)
@click.option("--glob", "use_glob", is_flag=True, default=False, help="Use glob syntax.")
@click.option(
    "--case-sensitive", is_flag=True, default=False, help="Enable case-sensitive matching."
)
@click.option(
    "--hide-values", is_flag=True, default=False, help="Omit values from output."
)
def search_run(
    pattern: str,
    vault_path: str,
    password: str,
    target: str,
    use_glob: bool,
    case_sensitive: bool,
    hide_values: bool,
) -> None:
    """Search PATTERN inside the vault at VAULT_PATH."""
    try:
        ciphertext = read_vault(vault_path)
    except FileNotFoundError:
        raise click.ClickException(f"Vault not found: {vault_path}")

    try:
        plaintext = decrypt(ciphertext, password)
    except Exception:
        raise click.ClickException("Decryption failed — wrong password or corrupted vault.")

    env = parse_env(plaintext.decode())

    kwargs = dict(glob=use_glob, case_sensitive=case_sensitive)

    if target == "keys":
        results = search_keys(env, pattern, **kwargs)
    elif target == "values":
        results = search_values(env, pattern, **kwargs)
    else:
        results = search_all(env, pattern, **kwargs)

    if not results:
        click.echo("No matches found.")
        return

    click.echo(f"Found {len(results)} match(es):\n")
    click.echo(format_results(results, show_values=not hide_values))
