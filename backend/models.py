import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from db import Base


class PromptProfile(Base):
    __tablename__ = "prompt_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    source_image_hash = Column(String(64), nullable=True)
    headers = Column(JSONB, nullable=False)
    column_count = Column(Integer, nullable=False)
    column_notes = Column(JSONB, nullable=False, default=list)
    row_rules = Column(JSONB, nullable=False, default=list)
    output_rules = Column(JSONB, nullable=False, default=list)
    active = Column(Boolean, default=False, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False)


class ProfileSettings(Base):
    __tablename__ = "profile_settings"

    id = Column(Integer, primary_key=True, default=1)
    active_profile_id = Column(UUID(as_uuid=True), ForeignKey("prompt_profiles.id"), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class TaskRecord(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String(32), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("prompt_profiles.id"), nullable=True)
    total_files = Column(Integer, default=0, nullable=False)
    processed_files = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    fail_count = Column(Integer, default=0, nullable=False)
    output_file = Column(String(255), nullable=True)
    message = Column(String(500), nullable=True)


class UploadRecord(Base):
    __tablename__ = "uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_uploads_task_file", "task_id", "file_path"),
    )


class ExtractedTable(Base):
    __tablename__ = "extracted_tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id"), nullable=False)
    headers = Column(JSONB, nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class ExtractedRow(Base):
    __tablename__ = "extracted_rows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey("extracted_tables.id"), nullable=False)
    row_index = Column(Integer, nullable=False)
    row_data = Column(JSONB, nullable=False)

    __table_args__ = (
        Index("ix_extracted_rows_table_index", "table_id", "row_index"),
    )
