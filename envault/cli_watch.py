"""CLI command: ``envault watch`` — re-lock a .env file on every save."""

from __future__ import annotations

import threading
from pathlib import Path

import click

from envault.cli import _get_backend
from envault.vault import write_vault
from envault.parser import parse_env
from envault.watch import watch


@click.command("watch")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--vault-dir", default=".envault", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Encryption password.")
@click.option("--interval", default=1.0, show_default=True, type=float, help="Poll interval (s).")
@click.option("--backend", default="local", show_default=True, type=click.Choice(["local", "s3"]), help="Storage backend.")
def watch_cmd(
    env_file: str,
    vault_dir: str,
    password: str,
    interval: float,
    backend: str,
) -> None:
    """Watch ENV_FILE and re-encrypt it into the vault on every save."""
    env_path = Path(env_file)
    vdir = Path(vault_dir)
    be = _get_backend(backend, vdir)

    click.echo(f"Watching {env_path} — press Ctrl-C to stop.")

    stop = threading.Event()

    def _on_change(path: Path) -> None:
        try:
            env = parse_env(path.read_text())
            meta = write_vault(vdir, env, password)
            click.echo(f"  [re-locked] version={meta['version']}  file={path}")
        except Exception as exc:  # noqa: BLE001
            click.echo(f"  [error] {exc}", err=True)

    try:
        watch(env_path, _on_change, interval=interval, stop_event=stop)
    except KeyboardInterrupt:
        stop.set()
        click.echo("Stopped watching.")
