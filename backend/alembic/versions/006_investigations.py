"""investigations and investigation_steps tables

Revision ID: 006
Revises: 005
Create Date: 2026-07-18
"""
import sqlalchemy as sa

from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="running"),
        sa.Column("conclusion", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_investigations_analysis_id", "investigations", ["analysis_id"])
    op.create_index("ix_investigations_user_id", "investigations", ["user_id"])

    op.create_table(
        "investigation_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("investigation_id", sa.String(36), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("agent", sa.String(16), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_investigation_steps_investigation_id", "investigation_steps", ["investigation_id"])


def downgrade() -> None:
    op.drop_table("investigation_steps")
    op.drop_table("investigations")
