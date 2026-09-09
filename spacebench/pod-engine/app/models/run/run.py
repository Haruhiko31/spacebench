import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Float, Index, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from ...enums import *


class UploadedFile(Base):
    __tablename__ = "files"
    __table_args__ = {"schema": "pod"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_name: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(512))
    file_type: Mapped[FileType] = mapped_column(Enum(FileType, schema="pod"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    validation_metadata = mapped_column(JSON, nullable=True)


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        Index("ix_runs_created_at", "created_at"),
        {"schema": "pod"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    mission_name: Mapped[str]= mapped_column(String(255))
    mission_year: Mapped[int] = mapped_column(Integer, nullable=False)
    mission_day: Mapped[int] = mapped_column(Integer, nullable=False)
    orbital_model: Mapped[OrbitalModel] = mapped_column(Enum(OrbitalModel, schema="pod"))
    estimator_type: Mapped[EstimatorType] = mapped_column(Enum(EstimatorType, schema="pod"))
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus, schema="pod"), default=RunStatus.pending)
    logs: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    rinex_file_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("pod.files.id"), nullable=False)
    gnss_sp3_file_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("pod.files.id"), nullable=False)
    gnss_clk_file_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("pod.files.id"), nullable=False)
    estimator_file_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("pod.files.id"), nullable=True)
    rms_3d: Mapped[str | None] = mapped_column(Float, nullable=True)
    rms_radial: Mapped[str | None] = mapped_column(Float, nullable=True)
    rms_along: Mapped[str | None] = mapped_column(Float, nullable=True)
    rms_cross: Mapped[str | None] = mapped_column(Float, nullable=True)

class RunRsoFile(Base):
    __tablename__ = "run_rso_files"
    __table_args__ = {"schema": "pod"}

    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pod.runs.id", ondelete="CASCADE"),
        primary_key=True,
    )

    file_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pod.files.id", ondelete="CASCADE"),
        primary_key=True,
    )

class RunLog(Base):
    __tablename__ = "run_logs"
    __table_args__ = {"schema": "pod"}
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("pod.runs.id"))
    level: Mapped[LogLevel] = mapped_column(Enum(LogLevel, schema="pod"))
    phase: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))



