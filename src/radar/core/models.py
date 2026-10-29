"""Domain data models and Pydantic v2 validation contracts for Trend Horizon Radar."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class QECategory(StrEnum):
    """The 6 core SDLC Quality Engineering pillars (Reference Domain Profile)."""

    SPEC_AND_MODEL = "Spec & Model"
    TEST_SYNTHESIS = "Test Synthesis"
    EXECUTION_AND_OPTIMIZATION = "Execution & Optimization"
    TRIAGE_AND_FIX = "Triage & Self-Healing"
    AGENT_SYSTEMS = "Agent Systems"
    GOVERNANCE_AND_EVALS = "Governance & Evals"


class TrackType(StrEnum):
    """Dual-track taxonomy: deterministic software testing vs non-deterministic AI evaluation."""

    TESTING = "testing"
    EVALUATION = "evaluation"


class EvidenceTier(StrEnum):
    """Evidence backing tiers for technical claims."""

    ACADEMIC_PEER_REVIEWED = "Academic Peer-Reviewed"
    OPEN_SOURCE_REPO = "Open Source Repo"
    ENGINEERING_POST_MORTEM = "Engineering Post-Mortem"
    VENDOR_ANNOUNCEMENT = "Vendor Announcement"


class RadarRing(StrEnum):
    """Tech Radar rings based on viability, validity, and operational ergonomics."""

    ADOPT = "Adopt"
    TRIAL = "Trial"
    ASSESS = "Assess"
    HOLD = "Hold"


class LifecycleStage(StrEnum):
    """Trend lifecycle trajectory based on engagement velocity and consensus."""

    EMERGING = "Emerging"
    CONSOLIDATED = "Consolidated"
    FADING = "Fading"


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
    engagement_metrics: dict[str, float] = Field(default_factory=dict)


class NoiseFilterResult(BaseModel):
    """Result of Stage 1 heuristic noise filtering."""

    payload_id: UUID
    passed: bool
    noise_score: float = Field(..., ge=0.0, le=1.0)
    domain_relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)
    matched_hype_indicators: list[str] = Field(default_factory=list)
    matched_credibility_indicators: list[str] = Field(default_factory=list)
    matched_relevance_indicators: list[str] = Field(default_factory=list)
    matched_financial_red_flags: list[str] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class QualifiedSignal(BaseModel):
    """Normalized signal that passed Stage 1 noise filtering and qualifies for Stage 2."""

    id: UUID = Field(default_factory=uuid4)
    payload: SourcePayload
    noise_score: float = Field(..., ge=0.0, le=1.0)
    quality_markers: list[str] = Field(default_factory=list)
    passed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExtractedInnovation(BaseModel):
    """Structured technical claims and domain classification extracted by Stage 2."""

    name: str = Field(..., description="Canonical entity / tool / research paper name")
    track: TrackType = Field(
        default=TrackType.TESTING,
        description="Domain track: testing (deterministic software) or evaluation (non-deterministic AI)",
    )
    category: QECategory = Field(..., description="Primary QE domain pillar")
    evidence_tier: EvidenceTier = Field(..., description="Backing evidence tier")
    is_qe_relevant: bool = Field(
        default=True,
        description="False if the topic is not software quality engineering, automated testing, or AI evaluation",
    )
    key_innovation: str = Field(
        ...,
        description="1-2 concise sentences summarizing the core technological breakthrough",
    )
    technical_claims: list[str] = Field(
        default_factory=list,
        description="2 to 5 verifiable, concrete technical claims made by authors/creators",
    )
    adequacy_evidence: list[str] = Field(
        default_factory=list,
        description="Verified adequacy indicators (e.g. mutation testing, property-based invariants, confidence score)",
    )
    has_reproducible_benchmark: bool = Field(
        default=False,
        description="Whether empirical benchmark or replication dataset is provided",
    )
    has_open_source_repo: bool = Field(
        default=False, description="Whether an accessible open-source code repository exists"
    )
    is_superficial_wrapper: bool = Field(
        default=False,
        description="Whether the tool is a superficial wrapper without novel architecture",
    )


class SignalDossier(BaseModel):
    """Stage 2 structured technical extraction dossier."""

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    topic_id: UUID | None = None
    topic_name: str | None = None
    name: str
    track: TrackType = Field(default=TrackType.TESTING)
    category: QECategory
    source_url: str
    evidence_tier: EvidenceTier
    is_qe_relevant: bool = Field(default=True)
    key_innovation: str
    technical_claims: list[str] = Field(default_factory=list)
    adequacy_evidence: list[str] = Field(default_factory=list)
    has_reproducible_benchmark: bool = False
    has_open_source_repo: bool = False
    is_superficial_wrapper: bool = False
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    embedding: list[float] | None = None
    engagement_metrics: dict[str, float] = Field(default_factory=dict)


class CommitteeAuditResult(BaseModel):
    """Structured LLM response schema for multi-lens adversarial evaluation."""

    security_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Security & Privacy viability score (0.0=critical blocker, 1.0=fully compliant)",
    )
    cicd_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Operational & CI/CD feasibility score (0.0=unusable/non-deterministic, 1.0=seamless)",
    )
    qe_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Technical rigor & empirical problem-solving score (0.0=synthetic toy, 1.0=rigorous breakthrough)",
    )
    security_critique: str = Field(
        ...,
        description="Adversarial critique from the Enterprise Security & Privacy Architect",
    )
    cicd_critique: str = Field(
        ...,
        description="Adversarial critique from the Enterprise DevOps & CI/CD Operations Lead",
    )
    qe_critique: str = Field(
        ...,
        description="Adversarial critique from the Principal AI Quality Engineering Architect",
    )
    skeptic_critique: str = Field(
        ...,
        description="Unified consensus critique synthesizing trade-offs, deployment hurdles, and bottom-line verdict",
    )
    enterprise_risks: list[str] = Field(
        default_factory=list,
        description="Concrete enterprise risk flags (e.g. data exfiltration, non-determinism, GPU memory cost)",
    )
    prerequisites: list[str] = Field(
        default_factory=list,
        description="Mandatory architectural prerequisites before enterprise adoption",
    )


class EnterpriseEvaluation(BaseModel):
    """Stage 3 multi-lens committee audit critique (Option 2C)."""

    id: UUID = Field(default_factory=uuid4)
    dossier_id: UUID
    # Multi-lens sub-scores (Weights: Security 35%, Operations 35%, Technical 30%)
    security_score: float = Field(..., ge=0.0, le=1.0)
    cicd_score: float = Field(..., ge=0.0, le=1.0)
    qe_score: float = Field(..., ge=0.0, le=1.0)
    composite_viability_score: float = Field(..., ge=0.0, le=1.0)
    enterprise_risks: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    # Detailed lens critiques
    security_critique: str | None = None
    cicd_critique: str | None = None
    qe_critique: str | None = None
    skeptic_critique: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SynthesizedTopic(BaseModel):
    """Structured LLM synthesis for a converged trend topic cluster."""

    name: str = Field(..., description="Canonical unified topic name")
    summary: str = Field(..., description="2-3 sentence technical summary of the converged trend")
    primary_category: QECategory = Field(..., description="Consensus QE domain pillar")


class ConvergenceResult(BaseModel):
    """Result of Stage 3 topic convergence and wrapper audit for a single dossier."""

    dossier_id: UUID
    topic_id: UUID
    is_new_topic: bool
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    is_wrapper: bool = False
    wrapper_penalty_applied: float = 0.0
    multi_source_consensus: bool = False
    corroboration_count: int = 1


class TrendTopic(BaseModel):
    """Synthesized cross-source trend topic entity (Option 3B)."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    track: TrackType = Field(default=TrackType.TESTING)
    category: QECategory
    summary: str
    corroboration_count: int = 1
    sources: list[str] = Field(default_factory=list)
    average_viability: float = Field(0.0, ge=0.0, le=1.0)
    average_validity: float = Field(0.0, ge=0.0, le=1.0)
    lifecycle_stage: LifecycleStage = LifecycleStage.EMERGING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RadarItem(BaseModel):
    """Stage 4 final radar publication entity."""

    id: UUID = Field(default_factory=uuid4)
    topic_id: UUID | None = None
    topic_name: str | None = None
    name: str
    track: TrackType = Field(default=TrackType.TESTING)
    category: QECategory
    source_url: str
    evidence_tier: EvidenceTier
    hype_score: float = Field(..., ge=0.0, le=1.0)
    viability_score: float = Field(..., ge=0.0, le=1.0)
    validity_score: float = Field(..., ge=0.0, le=1.0)
    recommended_ring: RadarRing
    lifecycle_stage: LifecycleStage = LifecycleStage.EMERGING
    corroboration_count: int = 1
    velocity_score: float = 0.0
    corroborating_sources: list[str] = Field(default_factory=list)
    key_innovation: str
    enterprise_risks: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    dossier_id: UUID | None = None
    evaluation_id: UUID | None = None
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    active: bool = True
