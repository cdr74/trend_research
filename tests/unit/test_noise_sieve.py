"""Unit tests and golden regression benchmark for the Stage 1 Heuristic Noise Sieve."""

from radar.core.models import SourcePayload, SourceType
from radar.pipeline.noise_sieve import NoiseSieve

GENUINE_TECHNICAL_SIGNALS = [
    (
        "Automated Mutation Testing for Autonomous Driving Systems",
        "Empirical evaluation using mutation score, ground truth dataset, and ablation analysis on 50k lines of code.",
        SourceType.ARXIV,
        1.3,
    ),
    (
        "Property-Based Fuzzing of Smart Contract Protocols",
        "Formal verification using symbolic execution and hypothesis property-based testing with statistical significance.",
        SourceType.ARXIV,
        1.3,
    ),
    (
        "Building Safe Canary Deployments with Automated Verification",
        "Statistical analysis of metrics across canary and baseline clusters. Automated canary analysis reduces outage blast radius.",
        SourceType.RSS,
        1.25,
    ),
    (
        "Predictive Test Selection at Scale in Enterprise Monorepo",
        "Using machine learning to select relevant regression tests. False positive rate and test duration reduced by 40%.",
        SourceType.RSS,
        1.25,
    ),
    (
        "microsoft/playwright",
        "Fast and reliable end-to-end testing for modern web apps. Hermetic execution and browser automation controller.",
        SourceType.GITHUB,
        1.1,
    ),
    (
        "boxed/mutmut",
        "Mutation testing system for Python 3. Calculates mutant killed percentage and test suite coverage effectiveness.",
        SourceType.GITHUB,
        1.1,
    ),
    (
        "google/fuzzbench",
        "Fuzzer benchmarking platform with statistical significance evaluation, coverage analysis, and reproducible artifacts.",
        SourceType.GITHUB,
        1.1,
    ),
    (
        "Chaos Engineering in the Cloud Era: Fault Injection at Scale",
        "Production post-mortem and chaos experiment injecting network latency into critical microservices.",
        SourceType.RSS,
        1.25,
    ),
    (
        "Contract Testing with Pact for Distributed Microservices",
        "API contract verification, consumer-driven contracts, and CI/CD pipeline integration to prevent breaking schema changes.",
        SourceType.RSS,
        1.2,
    ),
    (
        "Empirical Study of LLM-Assisted Automated Test Generation",
        "Controlled experiment comparing generated unit tests with human-authored suites using branch coverage and precision/recall.",
        SourceType.ARXIV,
        1.3,
    ),
]

HYPE_AND_SPAM_SIGNALS = [
    (
        "Top 10 AI Tools to Replace All Developers 100x Faster!",
        "Revolutionary magic bullet eliminates all engineering work. Click here to buy with promo code 'AI100'.",
        SourceType.MANUAL,
        0.8,
    ),
    (
        "Revolutionary Miracle Tool Eliminates 100% of All Bugs Guaranteed!",
        "Zero bugs guaranteed! Never write a unit test again. Instant migration with zero configuration required.",
        SourceType.MANUAL,
        0.8,
    ),
    (
        "Best AI Tools You Must Try Today to 10x Your Productivity",
        "This game-changing disruptive tool does all testing without human oversight. Check out our affiliate link for 50% discount.",
        SourceType.RSS,
        0.9,
    ),
    (
        "100x Faster QA: The Unprecedented AI Paradigm Shift",
        "Replaces all QA testers completely. Groundbreaking breakthrough that solves software quality forever.",
        SourceType.MANUAL,
        0.8,
    ),
    (
        "Top 5 Testing Tools That Everyone is Talking About",
        "Exclusive limited time offer: use coupon code 'TESTMAGIC' for instant migration to autonomous AGI testing.",
        SourceType.RSS,
        0.9,
    ),
    (
        "Disruptive Miracle Engine: 100% Bug-Free Software in 5 Minutes",
        "The revolutionary silver bullet for enterprise software engineering. Buy now before prices increase.",
        SourceType.MANUAL,
        0.8,
    ),
    (
        "Why AI Coding Replaces All Software Engineers Overnight",
        "Unprecedented paradigm shift will make developers obsolete. Sign up through our affiliate link today.",
        SourceType.MANUAL,
        0.8,
    ),
    (
        "Guaranteed No Bugs: The 100x Faster Magic Bullet",
        "Instant migration without human oversight. Top 10 reasons this tool makes all other testing obsolete.",
        SourceType.MANUAL,
        0.8,
    ),
    (
        "The Ultimate Autonomous Testing Revolution You Must Buy",
        "Promo code 'SAVE50' gives you access to the revolutionary software that eliminates all QA jobs.",
        SourceType.MANUAL,
        0.8,
    ),
    (
        "Top AI Testing Tools of 2026: Zero Effort Required",
        "Check our affiliate link below. 100x faster than humans with 100% bug-free guarantees.",
        SourceType.RSS,
        0.9,
    ),
]


def test_noise_sieve_high_signal_academic_paper_passes() -> None:
    sieve = NoiseSieve()
    payload = SourcePayload(
        source_type=SourceType.ARXIV,
        source_url="https://arxiv.org/abs/2410.18021",
        title="Automated Mutation Testing for Autonomous Driving Systems",
        raw_content="Empirical evaluation using mutation score, ablation study, and replication package.",
    )
    result, qualified = sieve.evaluate(payload, authority_weight=1.3)

    assert result.passed is True
    assert result.noise_score <= 0.25
    assert qualified is not None
    assert qualified.noise_score == result.noise_score
    assert len(result.matched_credibility_indicators) >= 2


def test_noise_sieve_clickbait_listicle_drops() -> None:
    sieve = NoiseSieve()
    payload = SourcePayload(
        source_type=SourceType.MANUAL,
        source_url="https://example.com/spam",
        title="Top 10 AI Tools to Replace All Developers 100x Faster!",
        raw_content="Click here to buy with promo code 'AI100'. Guaranteed 100% bug-free software with zero effort.",
    )
    result, qualified = sieve.evaluate(payload, authority_weight=0.8)

    assert result.passed is False
    assert result.noise_score > 0.60
    assert qualified is None
    assert len(result.rejection_reasons) > 0
    assert any("multiplier" in r.lower() or "100x" in r.lower() for r in result.rejection_reasons)


def test_noise_sieve_authority_discount_impact() -> None:
    sieve = NoiseSieve()
    # Mild hype ("10x faster")
    title = "Compiler Optimization for Test Synthesis"
    content = "We achieve 10x faster test generation using AST parsing."

    high_auth_payload = SourcePayload(
        source_type=SourceType.ARXIV,
        source_url="https://arxiv.org/abs/123",
        title=title,
        raw_content=content,
    )
    low_auth_payload = SourcePayload(
        source_type=SourceType.MANUAL,
        source_url="https://blog.com/123",
        title=title,
        raw_content=content,
    )

    high_res, _ = sieve.evaluate(high_auth_payload, authority_weight=1.3)
    low_res, _ = sieve.evaluate(low_auth_payload, authority_weight=0.8)

    # High authority must have a strictly lower noise score than low authority
    assert high_res.noise_score < low_res.noise_score


def test_noise_sieve_precision_golden_benchmark() -> None:
    """Validate > 90% precision on 10 verified signals vs 10 synthetic hype signals."""
    sieve = NoiseSieve(drop_threshold=0.60)

    # 1. Genuine signals MUST pass
    passed_genuine = 0
    for title, content, src_type, auth_weight in GENUINE_TECHNICAL_SIGNALS:
        payload = SourcePayload(
            source_type=src_type,
            source_url="https://example.com/item",
            title=title,
            raw_content=content,
        )
        res, qualified = sieve.evaluate(payload, authority_weight=auth_weight)
        if res.passed and qualified is not None:
            passed_genuine += 1

    # 2. Hype signals MUST drop
    dropped_hype = 0
    for title, content, src_type, auth_weight in HYPE_AND_SPAM_SIGNALS:
        payload = SourcePayload(
            source_type=src_type,
            source_url="https://example.com/item",
            title=title,
            raw_content=content,
        )
        res, qualified = sieve.evaluate(payload, authority_weight=auth_weight)
        if not res.passed and qualified is None:
            dropped_hype += 1

    # Assert precision
    genuine_pass_rate = passed_genuine / len(GENUINE_TECHNICAL_SIGNALS)
    hype_drop_rate = dropped_hype / len(HYPE_AND_SPAM_SIGNALS)

    assert genuine_pass_rate >= 0.90, f"Genuine pass rate was only {genuine_pass_rate:.1%}"
    assert hype_drop_rate >= 0.90, f"Hype drop rate was only {hype_drop_rate:.1%}"


def test_noise_sieve_batch_filtering() -> None:
    sieve = NoiseSieve()
    batch = [
        SourcePayload(
            source_type=SourceType.ARXIV,
            source_url="https://arxiv.org/abs/1",
            title="Mutation Testing in Rust",
            raw_content="Empirical evaluation and benchmark dataset.",
        ),
        SourcePayload(
            source_type=SourceType.MANUAL,
            source_url="https://spam.com/2",
            title="Top 10 AI Tools to Replace All Engineers",
            raw_content="Buy now with promo code SAVE50.",
        ),
    ]
    qualified, audit = sieve.filter_batch(batch, authority_weight=1.0)
    assert len(qualified) == 1
    assert qualified[0].payload.title == "Mutation Testing in Rust"
    assert len(audit) == 2
    assert audit[0].passed is True
    assert audit[1].passed is False


def test_noise_sieve_fallback_rejection_reason() -> None:
    # Trigger drop without specific hype words by lowering threshold below base noise
    sieve = NoiseSieve(drop_threshold=0.10, base_noise=0.15)
    payload = SourcePayload(
        source_type=SourceType.MANUAL,
        source_url="https://example.com/neutral",
        title="Plain Title",
        raw_content="Completely neutral content without buzzwords.",
    )
    res, qual = sieve.evaluate(payload, authority_weight=1.0)
    assert res.passed is False
    assert qual is None
    assert len(res.matched_hype_indicators) == 0
    assert "exceeded threshold" in res.rejection_reasons[0].lower()


def test_noise_sieve_financial_red_flag_testing_in_production_drops() -> None:
    """Validate that testing in production on live systems triggers a financial red flag and drops."""
    sieve = NoiseSieve()
    payload = SourcePayload(
        source_type=SourceType.RSS,
        source_url="https://example.com/chaos-prod",
        title="Testing in Production with Automated Chaos Fault Injection",
        raw_content="Why we execute continuous testing in production against live transaction databases.",
    )
    res, qual = sieve.evaluate(payload, authority_weight=1.0)
    assert res.passed is False
    assert qual is None
    assert any(
        "financial red flag: testing in production" in f.lower()
        for f in res.matched_financial_red_flags
    )
    assert any("testing in production" in r.lower() for r in res.rejection_reasons)


def test_noise_sieve_financial_red_flag_autonomous_merge_drops() -> None:
    """Validate that auto-merge without human oversight is flagged and dropped."""
    sieve = NoiseSieve()
    payload = SourcePayload(
        source_type=SourceType.GITHUB,
        source_url="https://github.com/example/auto-bot",
        title="AutoMerge Agent: Zero Human Oversight",
        raw_content="Automatic merge without human review for all synthesized unit tests.",
    )
    res, qual = sieve.evaluate(payload, authority_weight=1.0)
    assert res.passed is False
    assert qual is None
    assert any(
        "bypass of accountable human review" in f.lower() for f in res.matched_financial_red_flags
    )


def test_noise_sieve_evidence_of_adequacy_credit() -> None:
    """Validate that mutation scores and calibrated confidence scores receive credibility credits."""
    sieve = NoiseSieve()
    payload = SourcePayload(
        source_type=SourceType.ARXIV,
        source_url="https://arxiv.org/abs/2410.9999",
        title="Calibrated Confidence Scoring for Agentic Test Adequacy",
        raw_content="We provide verifiable proof of testing with mutation score analysis, automated test synthesis, and blast-radius quantification for CI/CD pipelines.",
    )
    res, qual = sieve.evaluate(payload, authority_weight=1.2)
    assert res.passed is True
    assert qual is not None
    assert res.noise_score <= 0.10
    assert any("adequacy" in c.lower() for c in res.matched_credibility_indicators)
    assert res.domain_relevance_score >= 0.70


def test_noise_sieve_non_se_domain_relevance_drops() -> None:
    """Validate that empirical non-SE papers (e.g. space weather, mathematics) drop on domain relevance."""
    sieve = NoiseSieve()
    payload = SourcePayload(
        source_type=SourceType.ARXIV,
        source_url="https://arxiv.org/abs/math.1234",
        title="Solving a 31-Year-Old Grand Challenge in Mathematics",
        raw_content="Empirical evaluation and controlled experiment proving the KLS conjecture in high-dimensional convex geometry.",
    )
    res, qual = sieve.evaluate(payload, authority_weight=1.3)
    assert res.passed is False
    assert qual is None
    assert res.domain_relevance_score < 0.35
    assert any("insufficient domain relevance" in r.lower() for r in res.rejection_reasons)
