"""Minimal TOML/environment configuration with explicit override precedence."""

import os
import tomllib
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, SecretStr
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from .common import ConfigurationError


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    database_url: SecretStr = SecretStr("postgresql+psycopg://localhost:5432/quont")
    raw_dir: Path = Path("data/raw")
    cache_dir: Path = Path("data/cache")
    exports_dir: Path = Path("data/exports")


def load_settings(
    config_file: Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    overrides: Mapping[str, object] | None = None,
) -> Settings:
    """Defaults -> optional TOML -> environment -> explicit CLI overrides.

    Relative paths resolve from the current working directory. .env loading is
    deliberately explicit: export its values into the shell before invoking CLI.
    """
    values: dict[str, object] = {}
    if config_file is not None:
        try:
            with config_file.open("rb") as source:
                values.update(tomllib.load(source))
        except (OSError, tomllib.TOMLDecodeError) as error:
            raise ConfigurationError("Could not load configuration TOML") from error
    environment = os.environ if environ is None else environ
    for key in Settings.model_fields:
        env_key = f"QUONT_{key.upper()}"
        if env_key in environment:
            values[key] = environment[env_key]
    if overrides:
        values.update(overrides)
    try:
        settings = Settings.model_validate(values)
        url = make_url(settings.database_url.get_secret_value())
        if url.drivername != "postgresql+psycopg":
            raise ConfigurationError("Database URL must use postgresql+psycopg")
        if not url.database:
            raise ConfigurationError("Database URL must select a database")
        paths = [
            path.resolve() for path in (settings.raw_dir, settings.cache_dir, settings.exports_dir)
        ]
        for index, path in enumerate(paths):
            for other in paths[index + 1 :]:
                if path.is_relative_to(other) or other.is_relative_to(path):
                    raise ConfigurationError("Raw, cache and export directories must not overlap")
    except (PydanticValidationError, ArgumentError, ValueError) as error:
        raise ConfigurationError("Invalid platform configuration") from error
    return settings
