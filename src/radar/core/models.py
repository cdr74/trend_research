"""Domain data models and Pydantic v2 validation contracts."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class QECategory(StrEnum):
    """The 6 core SDLC Quality Engineering pillars."""

    SPEC_AND_MODEL = "Spec & Model"
    TEST_SYNTHESIS = "Test Synthesis"
    EXECUTION_AND_OPTIMIZATION = "Execution & Optimization"
    TRIAGE_AND_FIX = "Triage & Self-Healing"
    AGENT_SYSTEMS = "Agent Systems"
    GOVERNANCE_AND_EVALS = "Governance & Evals"


class EvidenceTier(StrEnum):
    """Evidence backing tiers for technical claims."""

    ACADEMIC_PEER_REVIEWED = "Academic Peer-Reviewed"
    OPEN_SOURCE_REPO = "Open Source Repo"
    ENGINEERING_POST_MORTEM = "Engineering Post-Mortem"
    VENDOR_ANNOUNCEMENT = "Vendor Announcement"


class RadarRing(StrEnum):
    """Tech Radar rings based on enterprise viability and signal validity."""

    ADOPT = "Adopt"
    TRIAL = "Trial"
    ASSESS = "Assess"
    HOLD = "Hold"


class SourceType(StrEnum):
    """Supported ingestion source channels."""

    ARXIV = "arxiv"
    GITHUB = "github"
    RSS = "rss"
    MANUAL = "manual"


class SourcePayload(BaseModel):
    """Raw ingestion payload before Stage 1 noise filtering."""

    id: UUID = Field(default_factory=uuid4)
    source_type: SourceType
    source_url: str
    title: str
    raw_content: str
    author: str | None = None
    published_date: datetime | None = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class SignalDossier(BaseModel):
    """Stage 2 structured technical extraction dossier."""

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    name: str
    category: QECategory
    source_url: str
    evidence_tier: EvidenceTier
    key_innovation: str
    technical_claims: list[str] = Field(default_factory=list)
    has_reproducible_benchmark: bool = False
    has_open_source_repo: bool = False
    is_superficial_wrapper: bool = False
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    embedding: list[float] | None = None


class EnterpriseEvaluation(BaseModel):
    """Stage 3 adversarial enterprise banking audit critique (Committee 2C)."""

    id: UUID = Field(default_factory=uuid4)
    dossier_id: UUID
    # Persona sub-scores (Weights: Security 35%, CI/CD 35%, QE 30%)
    security_score: float = Field(..., ge=0.0, le=1.0)
    cicd_score: float = Field(..., ge=0.0, le=1.0)
    qe_score: float = Field(..., ge=0.0, le=1.0)
    composite_viability_score: float = Field(..., ge=0.0, le=1.0)
    enterprise_risks: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    # Detailed persona critiques
    security_critique: str | None = None
    cicd_critique: str | None = None
    qe_critique: str | None = None
    skeptic_critique: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RadarItem(BaseModel):
    """Stage 4 final radar publication entity."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    category: QECategory
    source_url: str
    evidence_tier: EvidenceTier
    hype_score: float = Field(..., ge=0.0, le=1.0)
    viability_score: float = Field(..., ge=0.0, le=1.0)
    validity_score: float = Field(..., ge=0.0, le=1.0)
    recommended_ring: RadarRing
    key_innovation: str
    enterprise_risks: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    dossier_id: UUID | None = None
    evaluation_id: UUID | None = None
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    active: bool = True
