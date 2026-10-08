from pathlib import Path

import pytest

from quont_sandbox.common import ConfigurationError
from quont_sandbox.configuration import load_settings


def test_precedence_and_secret_redaction(tmp_path: Path) -> None:
    assert load_settings(environ={}).raw_dir == Path("data/raw")
    config = tmp_path / "config.toml"
    config.write_text('raw_dir = "file/raw"', encoding="utf-8")
    assert load_settings(config, environ={}).raw_dir == Path("file/raw")
    assert load_settings(config, environ={"QUONT_RAW_DIR": "env/raw"}).raw_dir == Path("env/raw")
    settings = load_settings(
        config,
        environ={"QUONT_RAW_DIR": "env/raw"},
        overrides={
            "raw_dir": Path("cli/raw"),
            "database_url": "postgresql+psycopg://user:secret@localhost/quont",
        },
    )
    assert settings.raw_dir == Path("cli/raw")
    assert "secret" not in repr(settings)


def test_invalid_configuration_is_a_platform_error(tmp_path: Path) -> None:
    for overrides in (
        {"database_url": "sqlite:///local.db"},
        {"unknown": "value"},
        {"database_url": "bad secret url"},
        {"cache_dir": "data/raw/cache"},
    ):
        with pytest.raises(ConfigurationError):
            load_settings(environ={}, overrides=overrides)
    with pytest.raises(ConfigurationError):
        load_settings(tmp_path / "missing.toml", environ={})
    malformed = tmp_path / "bad.toml"
    malformed.write_text("[bad", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_settings(malformed, environ={})
