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


SAMPLE_GITHUB_ITEM_1: dict[str, object] = {
    "id": 123456,
    "name": "playwright",
    "full_name": "microsoft/playwright",
    "html_url": "https://github.com/microsoft/playwright",
    "description": "Fast and reliable end-to-end testing for modern web apps.",
    "owner": {"login": "microsoft"},
    "stargazers_count": 65000,
    "forks_count": 3500,
    "open_issues_count": 250,
    "language": "TypeScript",
    "topics": ["testing", "browser-automation", "end-to-end-testing"],
    "license": {"spdx_id": "Apache-2.0"},
    "default_branch": "main",
    "archived": False,
    "created_at": "2020-01-15T18:00:00Z",
    "pushed_at": "2026-10-23T12:00:00Z",
}

SAMPLE_GITHUB_ITEM_2: dict[str, object] = {
    "id": 789012,
    "name": "mutmut",
    "full_name": "boxed/mutmut",
    "html_url": "https://github.com/boxed/mutmut",
    "description": "Mutation testing system for Python 3.",
    "owner": {"login": "boxed"},
    "stargazers_count": 1200,
    "forks_count": 90,
    "open_issues_count": 30,
    "language": "Python",
    "topics": ["mutation-testing", "testing", "python"],
    "license": {"spdx_id": "BSD-3-Clause"},
    "default_branch": "master",
    "archived": False,
    "created_at": "2018-05-10T09:00:00Z",
    "pushed_at": "2026-10-10T15:00:00Z",
}

SAMPLE_GITHUB_SEARCH_RESPONSE: dict[str, object] = {
    "total_count": 2,
    "incomplete_results": False,
    "items": [SAMPLE_GITHUB_ITEM_1, SAMPLE_GITHUB_ITEM_2],
}


@pytest.fixture
def sample_github_response() -> dict[str, object]:
    """Sample GitHub repository search response fixture."""
    return SAMPLE_GITHUB_SEARCH_RESPONSE


SAMPLE_RSS_2_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Netflix Technology Blog</title>
    <link>https://netflixtechblog.com</link>
    <item>
      <title>Chaos Engineering in the Cloud Era</title>
      <link>https://netflixtechblog.com/chaos-engineering-cloud-era</link>
      <pubDate>Wed, 23 Oct 2026 14:00:00 GMT</pubDate>
      <dc:creator>Netflix Chaos Team</dc:creator>
      <category>Chaos Engineering</category>
      <category>Reliability</category>
      <description><![CDATA[<p>How we run continuous <b>verification</b> experiments against production clusters.</p>]]></description>
    </item>
    <item>
      <title>Building Safe Canary Deployments with Automated Verification</title>
      <link>https://netflixtechblog.com/safe-canary-deployments</link>
      <pubDate>Mon, 20 Oct 2026 10:30:00 GMT</pubDate>
      <dc:creator>John Doe</dc:creator>
      <category>Deployment</category>
      <description><![CDATA[Statistical analysis of metrics across canary and baseline clusters.]]></description>
    </item>
  </channel>
</rss>
"""


@pytest.fixture
def sample_rss_xml() -> str:
    """Sample RSS 2.0 XML fixture."""
    return SAMPLE_RSS_2_XML
