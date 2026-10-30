"""Signal ingestion engine and source collectors."""

from radar.ingestion.arxiv import (
    ArxivIngestor,
    parse_arxiv_atom_feed,
)
from radar.ingestion.base import (
    BaseIngestor,
    EngagementTelemetry,
    compute_engagement_velocity,
)
from radar.ingestion.community import (
    HnAlgoliaIngestor,
    parse_hn_story_item,
)
from radar.ingestion.github import (
    GithubIngestor,
    parse_github_repo_item,
    parse_github_search_response,
)
from radar.ingestion.rss import (
    RssFeedIngestor,
    parse_syndication_feed,
)
from radar.ingestion.sources import (
    SourceCatalog,
    SourceConfig,
    load_source_catalog,
)

__all__ = [
    "ArxivIngestor",
    "BaseIngestor",
    "EngagementTelemetry",
    "GithubIngestor",
    "HnAlgoliaIngestor",
    "RssFeedIngestor",
    "SourceCatalog",
    "SourceConfig",
    "compute_engagement_velocity",
    "load_source_catalog",
    "parse_arxiv_atom_feed",
    "parse_github_repo_item",
    "parse_github_search_response",
    "parse_hn_story_item",
    "parse_syndication_feed",
]
