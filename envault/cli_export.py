"""CLI sub-commands for exporting decrypted vault contents."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.crypto import decrypt
from envault.export import ExportFormat, export_env
from envault.parser import parse_env
from envault.vault import read_vault


@click.group("export")
def export_group() -> None:
    """Export decrypted env vars in various formats."""


@export_group.command("print")
@click.argument("vault_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format", "fmt",
    type=click.Choice(["shell", "docker", "json"]),
    default="shell",
    show_default=True,
    help="Output format.",
)
@click.option("--no-export", is_flag=True, default=False,
              help="Omit the 'export' keyword (shell format only).")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None,
              help="Write output to FILE instead of stdout.")
@click.password_option("--password", "-p", confirmation_prompt=False,
                       prompt="Vault password")
def export_print(
    vault_path: Path,
    fmt: ExportFormat,
    no_export: bool,
    output: Path | None,
    password: str,
) -> None:
    """Decrypt VAULT_PATH and print its contents in the chosen format."""
    try:
        ciphertext = read_vault(vault_path)
        plaintext = decrypt(ciphertext, password)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    env = parse_env(plaintext.decode())

    if fmt == "shell" and no_export:
        from envault.export import export_shell
        rendered = export_shell(env, export_keyword=False)
    else:
        rendered = export_env(env, fmt)

    if output:
        output.write_text(rendered)
        click.echo(f"Exported {len(env)} variable(s) to {output}")
    else:
        click.echo(rendered, nl=False)
