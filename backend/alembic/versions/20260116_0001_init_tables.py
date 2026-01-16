"""init tables

Revision ID: 20260116_0001
Revises:
Create Date: 2026-01-16 00:01:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260116_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prompt_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("source_image_hash", sa.String(length=64), nullable=True),
        sa.Column("headers", postgresql.JSONB(), nullable=False),
        sa.Column("column_count", sa.Integer(), nullable=False),
        sa.Column("column_notes", postgresql.JSONB(), nullable=False),
        sa.Column("row_rules", postgresql.JSONB(), nullable=False),
        sa.Column("output_rules", postgresql.JSONB(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
    )

    op.create_table(
        "profile_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("active_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["active_profile_id"], ["prompt_profiles.id"]),
    )

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("total_files", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("processed_files", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("success_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("fail_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("output_file", sa.String(length=255), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["prompt_profiles.id"]),
    )

    op.create_table(
        "uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
    )
    op.create_index("ix_uploads_task_file", "uploads", ["task_id", "file_path"])

    op.create_table(
        "extracted_tables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("headers", postgresql.JSONB(), nullable=False),
        sa.Column("row_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["upload_id"], ["uploads.id"]),
    )

    op.create_table(
        "extracted_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("table_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("row_data", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["table_id"], ["extracted_tables.id"]),
    )
    op.create_index("ix_extracted_rows_table_index", "extracted_rows", ["table_id", "row_index"])


def downgrade():
    op.drop_index("ix_extracted_rows_table_index", table_name="extracted_rows")
    op.drop_table("extracted_rows")
    op.drop_table("extracted_tables")
    op.drop_index("ix_uploads_task_file", table_name="uploads")
    op.drop_table("uploads")
    op.drop_table("tasks")
    op.drop_table("profile_settings")
    op.drop_table("prompt_profiles")
