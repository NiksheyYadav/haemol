from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locale: Mapped[str] = mapped_column(String(8), default="en")
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(16))
    locale: Mapped[str] = mapped_column(String(8), default="en")
    sex: Mapped[str] = mapped_column(String(16))
    age: Mapped[int] = mapped_column(Integer)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(24), default="pending")
    extraction_step: Mapped[str] = mapped_column(String(24), default="queued")
    status: Mapped[str] = mapped_column(String(24), default="pending")
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    extracted_params: Mapped[list["ExtractedParam"]] = relationship(back_populates="report", cascade="all, delete-orphan")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="report", cascade="all, delete-orphan")


class ExtractedParam(Base):
    __tablename__ = "extracted_params"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"))
    name: Mapped[str] = mapped_column(String(128))
    canonical_name: Mapped[str] = mapped_column(String(128))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    ref_range_key: Mapped[str] = mapped_column(String(128), default="")
    category: Mapped[str] = mapped_column(String(64), default="General")
    raw_reference_range: Mapped[str] = mapped_column(String(128), default="")
    range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    range_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    delta_from_range: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    report: Mapped["Report"] = relationship(back_populates="extracted_params")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"))
    model_name: Mapped[str] = mapped_column(String(64), default="ensemble")
    model_version: Mapped[str] = mapped_column(String(32), default="v3")
    summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(24), default="pending")
    conditions: Mapped[list[dict]] = mapped_column(JSON, default=list)
    abnormal_params: Mapped[list[dict]] = mapped_column(JSON, default=list)
    specialist_models: Mapped[list[dict]] = mapped_column(JSON, default=list)
    recommendations: Mapped[list[dict]] = mapped_column(JSON, default=list)
    confidence_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    report: Mapped["Report"] = relationship(back_populates="analyses")
    audio_jobs: Mapped[list["AudioJob"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class AudioJob(Base):
    __tablename__ = "audio_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"))
    language: Mapped[str] = mapped_column(String(24))
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="pending")
    fallback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    analysis: Mapped["Analysis"] = relationship(back_populates="audio_jobs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entity_id: Mapped[str] = mapped_column(String(36))
    entity_type: Mapped[str] = mapped_column(String(64))
    event: Mapped[str] = mapped_column(String(64))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"))
    sentiment: Mapped[str] = mapped_column(String(8))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class EventLog(Base):
    __tablename__ = "event_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(64))
    report_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    analysis_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
