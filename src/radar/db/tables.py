"""SQLAlchemy 2.0 ORM tables for PostgreSQL + pgvector persistence."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base class for Radar entities."""


class IngestedSourceTable(Base):
    """Raw ingestion records."""

    __tablename__ = "ingested_sources"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heuristic_noise_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )

    dossier: Mapped["SignalDossierTable | None"] = relationship(
        "SignalDossierTable", back_populates="source", uselist=False
    )


class SignalDossierTable(Base):
    """Stage 2 extracted dossiers with pgvector embeddings."""

    __tablename__ = "signal_dossiers"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ingested_sources.id"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_tier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    key_innovation: Mapped[str] = mapped_column(Text, nullable=False)
    technical_claims: Mapped[list[str]] = mapped_column(JSONB, default=list)
    has_reproducible_benchmark: Mapped[bool] = mapped_column(Boolean, default=False)
    has_open_source_repo: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superficial_wrapper: Mapped[bool] = mapped_column(Boolean, default=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    source: Mapped[IngestedSourceTable] = relationship(
        "IngestedSourceTable", back_populates="dossier"
    )
    evaluation: Mapped["EnterpriseEvaluationTable | None"] = relationship(
        "EnterpriseEvaluationTable", back_populates="dossier", uselist=False
    )


class EnterpriseEvaluationTable(Base):
    """Stage 3 adversarial banking evaluation critique."""

    __tablename__ = "enterprise_evaluations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    dossier_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("signal_dossiers.id"), unique=True, nullable=False
    )
    topology_score: Mapped[float] = mapped_column(Float, nullable=False)
    determinism_score: Mapped[float] = mapped_column(Float, nullable=False)
    privacy_score: Mapped[float] = mapped_column(Float, nullable=False)
    auditability_score: Mapped[float] = mapped_column(Float, nullable=False)
    composite_viability_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    enterprise_risks: Mapped[list[str]] = mapped_column(JSONB, default=list)
    prerequisites: Mapped[list[str]] = mapped_column(JSONB, default=list)
    skeptic_critique: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    dossier: Mapped[SignalDossierTable] = relationship(
        "SignalDossierTable", back_populates="evaluation"
    )
    radar_item: Mapped["RadarItemTable | None"] = relationship(
        "RadarItemTable", back_populates="evaluation", uselist=False
    )


class RadarItemTable(Base):
    """Stage 4 final radar publication entity."""

    __tablename__ = "radar_items"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    evaluation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("enterprise_evaluations.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_tier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    hype_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    viability_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    validity_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    recommended_ring: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    key_innovation: Mapped[str] = mapped_column(Text, nullable=False)
    enterprise_risks: Mapped[list[str]] = mapped_column(JSONB, default=list)
    prerequisites: Mapped[list[str]] = mapped_column(JSONB, default=list)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    evaluation: Mapped[EnterpriseEvaluationTable | None] = relationship(
        "EnterpriseEvaluationTable", back_populates="radar_item"
    )


# Indexes
Index("ix_radar_items_ring_category", RadarItemTable.recommended_ring, RadarItemTable.category)
