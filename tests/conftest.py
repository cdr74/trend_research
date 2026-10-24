"""Pytest fixtures and configuration."""

import pytest

from radar.core.config import LLMProviderType, Settings
from radar.providers.mock import MockProvider


@pytest.fixture
def mock_settings() -> Settings:
    """Fixture providing clean default settings."""
    return Settings(
        RADAR_LLM_PROVIDER=LLMProviderType.MOCK,
        RADAR_EMBEDDING_PROVIDER=LLMProviderType.MOCK,
    )


@pytest.fixture
def mock_provider() -> MockProvider:
    """Deterministic mock LLM provider."""
    return MockProvider(embedding_dim=128)


SAMPLE_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <link href="http://arxiv.org/api/query?search_query=cat%3Acs.SE&amp;id_list=&amp;start=0&amp;max_results=2" rel="self" type="application/atom+xml"/>
  <title type="html">ArXiv Query: search_query=cat:cs.SE</title>
  <id>http://arxiv.org/api/xyz123</id>
  <updated>2026-10-23T12:00:00Z</updated>
  <entry>
    <id>http://arxiv.org/abs/2410.18021v2</id>
    <updated>2026-10-22T17:49:15Z</updated>
    <published>2026-10-20T10:00:00Z</published>
    <title>
      Automated Mutation Testing
      for Autonomous Driving Systems
    </title>
    <summary>
      Mutation testing has emerged as a gold standard for assessing test suite
      quality. In this paper, we propose an automated mutation framework.
    </summary>
    <author>
      <name>Alice Smith</name>
    </author>
    <author>
      <name>Bob Jones</name>
    </author>
    <arxiv:doi>10.1145/1234567.890</arxiv:doi>
    <arxiv:comment>Accepted to ICSE 2026, 12 pages, 4 figures</arxiv:comment>
    <arxiv:journal_ref>ACM Transactions on Software Engineering 2026</arxiv:journal_ref>
    <link href="http://arxiv.org/abs/2410.18021v2" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2410.18021v2" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.SE" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.SE" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2410.19999v1</id>
    <updated>2026-10-18T08:00:00Z</updated>
    <published>2026-10-18T08:00:00Z</published>
    <title>Property-Based Fuzzing of Smart Contracts</title>
    <summary>We present a novel property-based fuzzing engine for Solidity contracts.</summary>
    <author>
      <name>Charlie Brown</name>
    </author>
    <author>
      <name>David Lee</name>
    </author>
    <author>
      <name>Elena Rostova</name>
    </author>
    <link href="http://arxiv.org/abs/2410.19999v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2410.19999v1" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.CR" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.CR" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.SE" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
"""


@pytest.fixture
def sample_arxiv_xml() -> str:
    """Sample arXiv XML response fixture."""
    return SAMPLE_ARXIV_XML
