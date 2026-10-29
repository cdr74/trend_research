"""SQLAlchemy 2.0 ORM tables for PostgreSQL + pgvector persistence."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base class for Radar entities."""


class IngestedSourceTable(Base):
    """Raw ingestion records with source engagement telemetry."""

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
    engagement_metrics: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )

    dossier: Mapped["SignalDossierTable | None"] = relationship(
        "SignalDossierTable", back_populates="source", uselist=False
    )


class TrendTopicTable(Base):
    """Synthesized multi-source trend topic cluster (Option 3B)."""

    __tablename__ = "trend_topics"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    track: Mapped[str] = mapped_column(String(50), default="testing", index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    corroboration_count: Mapped[int] = mapped_column(Integer, default=1, index=True)
    sources: Mapped[list[str]] = mapped_column(JSONB, default=list)
    average_viability: Mapped[float] = mapped_column(Float, default=0.0)
    average_validity: Mapped[float] = mapped_column(Float, default=0.0)
    lifecycle_stage: Mapped[str] = mapped_column(String(50), default="Emerging", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    dossiers: Mapped[list["SignalDossierTable"]] = relationship(
        "SignalDossierTable", back_populates="topic"
    )
    radar_items: Mapped[list["RadarItemTable"]] = relationship(
        "RadarItemTable", back_populates="topic"
    )


class SignalDossierTable(Base):
    """Stage 2 extracted dossiers with pgvector embeddings."""

    __tablename__ = "signal_dossiers"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ingested_sources.id"), unique=True, nullable=False
    )
    topic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("trend_topics.id"), nullable=True, index=True
    )
    topic_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    track: Mapped[str] = mapped_column(String(50), default="testing", index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_tier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_qe_relevant: Mapped[bool] = mapped_column(Boolean, default=True)
    key_innovation: Mapped[str] = mapped_column(Text, nullable=False)
    technical_claims: Mapped[list[str]] = mapped_column(JSONB, default=list)
    adequacy_evidence: Mapped[list[str]] = mapped_column(JSONB, default=list)
    has_reproducible_benchmark: Mapped[bool] = mapped_column(Boolean, default=False)
    has_open_source_repo: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superficial_wrapper: Mapped[bool] = mapped_column(Boolean, default=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    engagement_metrics: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    source: Mapped[IngestedSourceTable] = relationship(
        "IngestedSourceTable", back_populates="dossier"
    )
    topic: Mapped[TrendTopicTable | None] = relationship(
        "TrendTopicTable", back_populates="dossiers"
    )
    evaluation: Mapped["EnterpriseEvaluationTable | None"] = relationship(
        "EnterpriseEvaluationTable", back_populates="dossier", uselist=False
    )


class EnterpriseEvaluationTable(Base):
    """Stage 3 multi-lens committee evaluation critique (Option 2C)."""

    __tablename__ = "enterprise_evaluations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    dossier_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("signal_dossiers.id"), unique=True, nullable=False
    )
    security_score: Mapped[float] = mapped_column(Float, nullable=False)
    cicd_score: Mapped[float] = mapped_column(Float, nullable=False)
    qe_score: Mapped[float] = mapped_column(Float, nullable=False)
    composite_viability_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    enterprise_risks: Mapped[list[str]] = mapped_column(JSONB, default=list)
    prerequisites: Mapped[list[str]] = mapped_column(JSONB, default=list)
    security_critique: Mapped[str | None] = mapped_column(Text, nullable=True)
    cicd_critique: Mapped[str | None] = mapped_column(Text, nullable=True)
    qe_critique: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    topic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("trend_topics.id"), nullable=True, index=True
    )
    topic_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    track: Mapped[str] = mapped_column(String(50), default="testing", index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_tier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    hype_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    viability_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    validity_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    recommended_ring: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    lifecycle_stage: Mapped[str] = mapped_column(String(50), default="Emerging", index=True)
    corroboration_count: Mapped[int] = mapped_column(Integer, default=1, index=True)
    velocity_score: Mapped[float] = mapped_column(Float, default=0.0)
    corroborating_sources: Mapped[list[str]] = mapped_column(JSONB, default=list)
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
    topic: Mapped[TrendTopicTable | None] = relationship(
        "TrendTopicTable", back_populates="radar_items"
    )


# Indexes
Index("ix_radar_items_ring_category", RadarItemTable.recommended_ring, RadarItemTable.category)
