import io
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from quont_sandbox.assets import Asset
from quont_sandbox.assets.infrastructure.database import Base

ROOT = Path(__file__).resolve().parents[2]


def test_postgres_schema_compiles_without_server() -> None:
    assert set(Base.metadata.tables) == {"assets", "venues", "instruments", "external_identifiers"}
    assert not issubclass(Asset, Base)
    for table in Base.metadata.sorted_tables:
        sql = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        assert "UUID" in sql and "PRIMARY KEY" in sql
    assert len(Base.metadata.tables["instruments"].foreign_keys) == 2
    assert len(Base.metadata.tables["external_identifiers"].foreign_keys) == 1


def test_offline_migration_sql_matches_asset_schema() -> None:
    output = io.StringIO()
    config = Config(str(ROOT / "alembic.ini"), output_buffer=output)
    command.upgrade(config, "head", sql=True)
    sql = output.getvalue()
    for name in Base.metadata.tables:
        assert f"CREATE TABLE {name}" in sql
    assert "FOREIGN KEY" in sql and "ck_external_identifiers_interval" in sql
    assert "CREATE TABLE price_bars" not in sql
    assert "INSERT INTO alembic_version" in sql
