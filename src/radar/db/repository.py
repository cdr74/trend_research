"""Asynchronous repository for Radar persistence operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from radar.core.models import (
    EnterpriseEvaluation,
    LifecycleStage,
    QECategory,
    RadarItem,
    RadarRing,
    SignalDossier,
    SourcePayload,
    TrendTopic,
)
from radar.db.tables import (
    EnterpriseEvaluationTable,
    IngestedSourceTable,
    RadarItemTable,
    SignalDossierTable,
    TrendTopicTable,
)


class RadarRepository:
    """Async repository interacting with PostgreSQL and pgvector."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_source_payload(self, payload: SourcePayload) -> IngestedSourceTable:
        """Persist a raw ingested source payload with engagement metrics."""
        record = IngestedSourceTable(
            id=payload.id,
            source_type=payload.source_type.value,
            source_url=payload.source_url,
            title=payload.title,
            raw_content=payload.raw_content,
            author=payload.author,
            published_date=payload.published_date,
            meta=payload.metadata,
            engagement_metrics=payload.engagement_metrics,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_pending_sources(self, limit: int = 20) -> list[IngestedSourceTable]:
        """Fetch ingested sources pending evaluation."""
        stmt = (
            select(IngestedSourceTable)
            .where(IngestedSourceTable.status == "pending")
            .order_by(IngestedSourceTable.ingested_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save_topic(self, topic: TrendTopic) -> TrendTopicTable:
        """Persist a multi-source synthesized trend topic cluster."""
        record = TrendTopicTable(
            id=topic.id,
            name=topic.name,
            category=topic.category.value,
            summary=topic.summary,
            corroboration_count=topic.corroboration_count,
            sources=topic.sources,
            average_viability=topic.average_viability,
            average_validity=topic.average_validity,
            lifecycle_stage=topic.lifecycle_stage.value,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def save_dossier(self, dossier: SignalDossier) -> SignalDossierTable:
        """Persist a Stage 2 extracted technical dossier."""
        record = SignalDossierTable(
            id=dossier.id,
            source_id=dossier.source_id,
            topic_id=dossier.topic_id,
            name=dossier.name,
            category=dossier.category.value,
            source_url=dossier.source_url,
            evidence_tier=dossier.evidence_tier.value,
            key_innovation=dossier.key_innovation,
            technical_claims=dossier.technical_claims,
            has_reproducible_benchmark=dossier.has_reproducible_benchmark,
            has_open_source_repo=dossier.has_open_source_repo,
            is_superficial_wrapper=dossier.is_superficial_wrapper,
            embedding=dossier.embedding,
            engagement_metrics=dossier.engagement_metrics,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def save_evaluation(self, evaluation: EnterpriseEvaluation) -> EnterpriseEvaluationTable:
        """Persist a Stage 3 multi-lens committee evaluation."""
        record = EnterpriseEvaluationTable(
            id=evaluation.id,
            dossier_id=evaluation.dossier_id,
            security_score=evaluation.security_score,
            cicd_score=evaluation.cicd_score,
            qe_score=evaluation.qe_score,
            composite_viability_score=evaluation.composite_viability_score,
            enterprise_risks=evaluation.enterprise_risks,
            prerequisites=evaluation.prerequisites,
            security_critique=evaluation.security_critique,
            cicd_critique=evaluation.cicd_critique,
            qe_critique=evaluation.qe_critique,
            skeptic_critique=evaluation.skeptic_critique,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def save_radar_item(self, item: RadarItem) -> RadarItemTable:
        """Persist a Stage 4 final radar publication entity."""
        record = RadarItemTable(
            id=item.id,
            evaluation_id=item.evaluation_id,
            topic_id=item.topic_id,
            name=item.name,
            category=item.category.value,
            source_url=item.source_url,
            evidence_tier=item.evidence_tier.value,
            hype_score=item.hype_score,
            viability_score=item.viability_score,
            validity_score=item.validity_score,
            recommended_ring=item.recommended_ring.value,
            lifecycle_stage=item.lifecycle_stage.value,
            corroboration_count=item.corroboration_count,
            velocity_score=item.velocity_score,
            corroborating_sources=item.corroborating_sources,
            key_innovation=item.key_innovation,
            enterprise_risks=item.enterprise_risks,
            prerequisites=item.prerequisites,
            active=item.active,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def query_radar_items(
        self,
        ring: RadarRing | None = None,
        category: QECategory | None = None,
        lifecycle_stage: LifecycleStage | None = None,
        min_viability: float = 0.0,
        max_hype: float = 1.0,
    ) -> list[RadarItemTable]:
        """Query active radar items with multi-criteria filters."""
        stmt = (
            select(RadarItemTable)
            .where(RadarItemTable.active.is_(True))
            .where(RadarItemTable.viability_score >= min_viability)
            .where(RadarItemTable.hype_score <= max_hype)
        )
        if ring is not None:
            stmt = stmt.where(RadarItemTable.recommended_ring == ring.value)
        if category is not None:
            stmt = stmt.where(RadarItemTable.category == category.value)
        if lifecycle_stage is not None:
            stmt = stmt.where(RadarItemTable.lifecycle_stage == lifecycle_stage.value)

        stmt = stmt.order_by(RadarItemTable.viability_score.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_similar_dossiers(
        self, embedding: list[float], limit: int = 5, exclude_id: UUID | None = None
    ) -> list[SignalDossierTable]:
        """Perform semantic similarity search using pgvector cosine distance."""
        stmt = select(SignalDossierTable).where(SignalDossierTable.embedding.isnot(None))
        if exclude_id is not None:
            stmt = stmt.where(SignalDossierTable.id != exclude_id)

        # pgvector cosine distance: embedding <=> target_vector
        stmt = stmt.order_by(SignalDossierTable.embedding.cosine_distance(embedding)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
