"""CLI sub-commands for managing envault profiles (set / show / list / delete)."""

from __future__ import annotations

import json
import sys

import click

from envault.profiles import (
    delete_profile,
    list_profiles,
    load_profile,
    profile_exists,
    save_profile,
)


@click.group("profile")
def profile_group():
    """Manage named envault profiles."""


@profile_group.command("set")
@click.argument("name")
@click.option("--backend", type=click.Choice(["local", "s3"]), required=True, help="Storage backend.")
@click.option("--store-dir", default=None, help="Local store directory (local backend).")
@click.option("--bucket", default=None, help="S3 bucket name (s3 backend).")
@click.option("--prefix", default="", show_default=True, help="Key prefix inside the bucket.")
def profile_set(name: str, backend: str, store_dir: str | None, bucket: str | None, prefix: str):
    """Create or update a named profile."""
    config: dict = {"backend": backend, "prefix": prefix}
    if backend == "local":
        if not store_dir:
            raise click.UsageError("--store-dir is required for the local backend.")
        config["store_dir"] = store_dir
    elif backend == "s3":
        if not bucket:
            raise click.UsageError("--bucket is required for the s3 backend.")
        config["bucket"] = bucket
    save_profile(name, config)
    click.echo(f"Profile '{name}' saved.")


@profile_group.command("show")
@click.argument("name", default="default")
def profile_show(name: str):
    """Print the configuration for a profile as JSON."""
    try:
        config = load_profile(name)
    except KeyError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)
    click.echo(json.dumps(config, indent=2))


@profile_group.command("list")
def profile_list():
    """List all saved profiles."""
    names = list_profiles()
    if not names:
        click.echo("No profiles found.")
        return
    for name in names:
        click.echo(name)


@profile_group.command("delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this profile?")
def profile_delete(name: str):
    """Delete a named profile."""
    if delete_profile(name):
        click.echo(f"Profile '{name}' deleted.")
    else:
        click.echo(f"Profile '{name}' does not exist.", err=True)
        sys.exit(1)
