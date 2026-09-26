"""Initial schema — commodities, packaging_materials, commodity_packaging_map

Revision ID: 0001
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commodities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True, index=True),
        sa.Column("moisture_pct", sa.Float(), nullable=False),
        sa.Column("water_activity", sa.Float(), nullable=False),
        sa.Column("respiration_rate", sa.Float(), nullable=True),
        sa.Column("fat_content", sa.Float(), nullable=False),
        sa.Column("light_sensitivity", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("fragility", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "packaging_materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True, index=True),
        sa.Column("wvtr", sa.Float(), nullable=False),
        sa.Column("otr", sa.Float(), nullable=False),
        sa.Column("cost_per_unit", sa.Float(), nullable=False),
        sa.Column("biodegradability_score", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("typical_use_case", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("light_blocking", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("crush_resistance", sa.Integer(), nullable=False, server_default="3"),
    )

    op.create_table(
        "commodity_packaging_map",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("commodity_id", sa.Integer(), sa.ForeignKey("commodities.id"), nullable=False, index=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("packaging_materials.id"), nullable=False, index=True),
        sa.Column("suitability_score", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("commodity_id", "material_id", name="uq_commodity_material"),
    )


def downgrade() -> None:
    op.drop_table("commodity_packaging_map")
    op.drop_table("packaging_materials")
    op.drop_table("commodities")
