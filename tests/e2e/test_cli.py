from pathlib import Path

import pytest
from typer.testing import CliRunner

from quont_sandbox import __version__
from quont_sandbox.cli import app


@pytest.mark.parametrize("args", [["--help"], ["data", "--help"], ["assets", "--help"]])
def test_help(args: list[str]) -> None:
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Usage" in result.output


def test_version() -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0 and __version__ in result.output


def test_paths_and_config_errors(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["--raw-dir", str(tmp_path / "raw"), "data", "paths"])
    assert result.exit_code == 0 and str(tmp_path / "raw") in result.output
    assert not (tmp_path / "raw").exists()
    result = CliRunner().invoke(app, ["--database-url", "bad:secret", "data", "paths"])
    assert result.exit_code == 2
    assert "secret" not in result.output
