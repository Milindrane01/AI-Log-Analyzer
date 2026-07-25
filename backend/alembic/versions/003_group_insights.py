"""group_insights table

Revision ID: 003
Revises: 002
Create Date: 2026-07-18
"""

import sqlalchemy as sa

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "group_insights",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "group_id",
            sa.String(36),
            sa.ForeignKey("error_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("from_cache", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_group_insights_group_id", "group_insights", ["group_id"], unique=True)
    op.create_index("ix_group_insights_user_id", "group_insights", ["user_id"])
    op.create_index("ix_group_insights_fingerprint", "group_insights", ["fingerprint"])


def downgrade() -> None:
    op.drop_table("group_insights")
