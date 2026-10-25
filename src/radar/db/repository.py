"""Asynchronous repository for Radar persistence operations."""

from typing import Any
from uuid import UUID

from sqlalchemy import select, text
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
        """Persist a raw ingested source payload with engagement metrics (upsert)."""
        stmt = select(IngestedSourceTable).where(
            IngestedSourceTable.source_url == payload.source_url
        )
        res = await self.session.execute(stmt)
        existing = res.scalars().first()
        if existing is not None:
            existing.engagement_metrics = payload.engagement_metrics
            existing.raw_content = payload.raw_content
            existing.title = payload.title
            payload.id = existing.id
            await self.session.flush()
            return existing

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

    async def get_topic_by_id(self, topic_id: UUID) -> TrendTopicTable | None:
        """Retrieve a trend topic by primary key."""
        stmt = select(TrendTopicTable).where(TrendTopicTable.id == topic_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_topic(self, topic: TrendTopic) -> TrendTopicTable | None:
        """Update an existing trend topic with newly synthesized data."""
        record = await self.get_topic_by_id(topic.id)
        if record is not None:
            record.name = topic.name
            record.category = topic.category.value
            record.summary = topic.summary
            record.corroboration_count = topic.corroboration_count
            record.sources = topic.sources
            record.average_viability = topic.average_viability
            record.average_validity = topic.average_validity
            record.lifecycle_stage = topic.lifecycle_stage.value
            await self.session.flush()
        return record

    async def get_dossiers_for_topic(self, topic_id: UUID) -> list[SignalDossierTable]:
        """Retrieve all dossiers associated with a given topic."""
        stmt = select(SignalDossierTable).where(SignalDossierTable.topic_id == topic_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def assign_dossier_to_topic(self, dossier_id: UUID, topic_id: UUID) -> None:
        """Link a dossier to a topic."""
        stmt = select(SignalDossierTable).where(SignalDossierTable.id == dossier_id)
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if record is not None:
            record.topic_id = topic_id
            await self.session.flush()

    async def save_dossier(self, dossier: SignalDossier) -> SignalDossierTable:
        """Persist a Stage 2 extracted technical dossier (upsert)."""
        stmt = select(SignalDossierTable).where(SignalDossierTable.source_id == dossier.source_id)
        res = await self.session.execute(stmt)
        existing = res.scalars().first()
        if existing is not None:
            existing.name = dossier.name
            existing.category = dossier.category.value
            existing.evidence_tier = dossier.evidence_tier.value
            existing.key_innovation = dossier.key_innovation
            existing.technical_claims = dossier.technical_claims
            existing.has_reproducible_benchmark = dossier.has_reproducible_benchmark
            existing.has_open_source_repo = dossier.has_open_source_repo
            existing.is_superficial_wrapper = dossier.is_superficial_wrapper
            existing.embedding = dossier.embedding
            existing.engagement_metrics = dossier.engagement_metrics
            existing.topic_id = dossier.topic_id
            dossier.id = existing.id
            await self.session.flush()
            return existing

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
        """Persist a Stage 3 multi-lens committee evaluation (upsert)."""
        stmt = select(EnterpriseEvaluationTable).where(
            EnterpriseEvaluationTable.dossier_id == evaluation.dossier_id
        )
        res = await self.session.execute(stmt)
        existing = res.scalars().first()
        if existing is not None:
            existing.security_score = evaluation.security_score
            existing.cicd_score = evaluation.cicd_score
            existing.qe_score = evaluation.qe_score
            existing.composite_viability_score = evaluation.composite_viability_score
            existing.enterprise_risks = evaluation.enterprise_risks
            existing.prerequisites = evaluation.prerequisites
            existing.security_critique = evaluation.security_critique
            existing.cicd_critique = evaluation.cicd_critique
            existing.qe_critique = evaluation.qe_critique
            existing.skeptic_critique = evaluation.skeptic_critique
            evaluation.id = existing.id
            await self.session.flush()
            return existing

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
        """Persist a Stage 4 final radar publication entity (upsert)."""
        stmt = select(RadarItemTable).where(RadarItemTable.source_url == item.source_url)
        res = await self.session.execute(stmt)
        existing = res.scalars().first()
        if existing is not None:
            existing.name = item.name
            existing.category = item.category.value
            existing.evidence_tier = item.evidence_tier.value
            existing.hype_score = item.hype_score
            existing.viability_score = item.viability_score
            existing.validity_score = item.validity_score
            existing.recommended_ring = item.recommended_ring.value
            existing.lifecycle_stage = item.lifecycle_stage.value
            existing.corroboration_count = item.corroboration_count
            existing.velocity_score = item.velocity_score
            existing.corroborating_sources = item.corroborating_sources
            existing.key_innovation = item.key_innovation
            existing.enterprise_risks = item.enterprise_risks
            existing.prerequisites = item.prerequisites
            existing.active = item.active
            existing.evaluation_id = item.evaluation_id
            existing.topic_id = item.topic_id
            item.id = existing.id
            await self.session.flush()
            return existing

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

    async def get_radar_item_by_id(self, item_id: UUID) -> RadarItemTable | None:
        """Retrieve a specific radar item by primary key."""
        stmt = select(RadarItemTable).where(RadarItemTable.id == item_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_evaluation_by_id(self, evaluation_id: UUID) -> EnterpriseEvaluationTable | None:
        """Retrieve an evaluation record by primary key."""
        stmt = select(EnterpriseEvaluationTable).where(
            EnterpriseEvaluationTable.id == evaluation_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

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

    async def execute_raw_sql(self, sql_query: str) -> tuple[list[str], list[list[Any]]]:
        """Execute a raw SQL query and return column names and rows."""
        result = await self.session.execute(text(sql_query))
        columns = list(result.keys())
        if columns:
            rows = [list(row) for row in result.all()]
            return columns, rows
        return [], []

    async def get_items_with_embeddings(self) -> list[tuple[RadarItemTable, list[float] | None]]:
        """Retrieve all active radar items alongside their signal embeddings if available."""
        stmt = (
            select(RadarItemTable, SignalDossierTable.embedding)
            .outerjoin(
                EnterpriseEvaluationTable,
                RadarItemTable.evaluation_id == EnterpriseEvaluationTable.id,
            )
            .outerjoin(
                SignalDossierTable,
                EnterpriseEvaluationTable.dossier_id == SignalDossierTable.id,
            )
            .where(RadarItemTable.active.is_(True))
            .order_by(RadarItemTable.viability_score.desc())
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]
