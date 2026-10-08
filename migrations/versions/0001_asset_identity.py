"""Initial asset identity hierarchy.

Revision ID: 0001
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("asset_class", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("asset_id"),
        sa.CheckConstraint(
            "asset_class IN ('EQUITY', 'ETF', 'CRYPTO')", name="ck_assets_asset_class"
        ),
    )
    op.create_table(
        "venues",
        sa.Column("venue_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("venue_id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "instruments",
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("venue_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("instrument_id"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.asset_id"]),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.venue_id"]),
    )
    op.create_index("ix_instruments_asset_id", "instruments", ["asset_id"])
    op.create_index("ix_instruments_venue_id", "instruments", ["venue_id"])
    op.create_table(
        "external_identifiers",
        sa.Column("identifier_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("namespace", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("identifier_id"),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.instrument_id"]),
        sa.UniqueConstraint(
            "instrument_id",
            "namespace",
            "value",
            "valid_from",
            name="uq_external_identifiers_interval",
        ),
        sa.CheckConstraint(
            "valid_to IS NULL OR valid_to > valid_from", name="ck_external_identifiers_interval"
        ),
    )
    op.create_index(
        "ix_external_identifiers_instrument_id", "external_identifiers", ["instrument_id"]
    )


def downgrade() -> None:
    op.drop_table("external_identifiers")
    op.drop_table("instruments")
    op.drop_table("venues")
    op.drop_table("assets")
