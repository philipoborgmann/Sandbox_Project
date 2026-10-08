"""Data CLI adapter."""

import typer

from quont_sandbox.application import storage_directories
from quont_sandbox.configuration import Settings

app = typer.Typer(help="Data Platform and local storage.", no_args_is_help=True)


@app.command()
def paths(context: typer.Context) -> None:
    """Display raw, cache and export directories without creating them."""
    settings = context.obj
    assert isinstance(settings, Settings)
    directories = storage_directories(settings)
    typer.echo(f"raw: {directories.raw}")
    typer.echo(f"cache: {directories.cache}")
    typer.echo(f"exports: {directories.exports}")
