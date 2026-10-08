"""Central Typer CLI with module-owned command registration."""

from pathlib import Path
from typing import Annotated

import typer

from quont_sandbox import __version__
from quont_sandbox.common import ConfigurationError
from quont_sandbox.configuration import load_settings

from .assets import app as assets_app
from .data import app as data_app

app = typer.Typer(
    help="Quont Sandbox — local quantitative research foundation.", no_args_is_help=True
)
app.add_typer(assets_app, name="assets")
app.add_typer(data_app, name="data")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"quont {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    context: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=version_callback, is_eager=True, help="Show version and exit."
        ),
    ] = False,
    config: Annotated[
        Path | None, typer.Option("--config", help="Optional TOML configuration.")
    ] = None,
    database_url: Annotated[
        str | None, typer.Option("--database-url", help="PostgreSQL URL override.")
    ] = None,
    raw_dir: Annotated[Path | None, typer.Option("--raw-dir")] = None,
    cache_dir: Annotated[Path | None, typer.Option("--cache-dir")] = None,
    exports_dir: Annotated[Path | None, typer.Option("--exports-dir")] = None,
) -> None:
    overrides: dict[str, object] = {}
    for key, value in (
        ("database_url", database_url),
        ("raw_dir", raw_dir),
        ("cache_dir", cache_dir),
        ("exports_dir", exports_dir),
    ):
        if value is not None:
            overrides[key] = value
    try:
        context.obj = load_settings(config, overrides=overrides)
    except ConfigurationError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
