"""Asset catalogue CLI adapter."""

import typer

from quont_sandbox.application import read_asset_catalogue
from quont_sandbox.common import QuontSandboxError
from quont_sandbox.configuration import Settings

app = typer.Typer(help="Asset identity and reference catalogue.", no_args_is_help=True)


@app.command("list")
def list_command(context: typer.Context) -> None:
    """List stable asset identities from the configured PostgreSQL catalogue."""
    settings = context.obj
    assert isinstance(settings, Settings)
    try:
        assets = read_asset_catalogue(settings)
    except QuontSandboxError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    for asset in assets:
        typer.echo(f"{asset.asset_id}\t{asset.asset_class.value}\t{asset.name}")
