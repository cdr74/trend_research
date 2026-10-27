"""Stage 1 deterministic heuristic noise sieve and anti-hype classifier."""

import re

from radar.core.models import NoiseFilterResult, QualifiedSignal, SourcePayload

# Hype indicators: (compiled_regex, penalty_weight, description)
HYPE_RULES: list[tuple[re.Pattern[str], float, str]] = [
    (
        re.compile(
            r"\b(?:100x|10x|50x|1000x)\s+(?:faster|more productive|productivity|improvement|quicker)\b",
            re.IGNORECASE,
        ),
        0.25,
        "Exaggerated multiplier velocity claim",
    ),
    (
        re.compile(
            r"\b(?:revolutionary|game[- ]changing|miraculous|magic bullet|silver bullet|disruptive innovation)\b",
            re.IGNORECASE,
        ),
        0.20,
        "Hyperbolic superlative phrasing",
    ),
    (
        re.compile(
            r"\b(?:replaces? all (?:software )?(?:engineers?|developers?|testers?|qa|jobs?))\b",
            re.IGNORECASE,
        ),
        0.35,
        "Absolute developer/QA replacement claim",
    ),
    (
        re.compile(
            r"\b(?:100% bug[- ]free|zero bugs?(?: guaranteed)?|zero defects?(?: guaranteed)?|guaranteed no bugs)\b",
            re.IGNORECASE,
        ),
        0.35,
        "Absolute defect elimination guarantee",
    ),
    (
        re.compile(
            r"\b(?:affiliate link|discount code|promo code|coupon code|buy now|limited time offer)\b",
            re.IGNORECASE,
        ),
        0.40,
        "Commercial affiliate/promotional monetization pattern",
    ),
    (
        re.compile(
            r"\b(?:top \d+ (?:best )?(?:ai )?tools (?:you must|everyone is talking about|to try|of \d{4}))\b",
            re.IGNORECASE,
        ),
        0.30,
        "Clickbait aggregator listicle format",
    ),
    (
        re.compile(
            r"\b(?:instant migration|zero effort|zero configuration required|without human oversight)\b",
            re.IGNORECASE,
        ),
        0.20,
        "Unsubstantiated effortless deployment claim",
    ),
    (
        re.compile(
            r"\b(?:groundbreaking breakthrough|unprecedented paradigm shift)\b",
            re.IGNORECASE,
        ),
        0.15,
        "Marketing inflation buzzwords",
    ),
    # Financial Enterprise Red-Flag Rules (Ref: ADR-0021)
    (
        re.compile(
            r"\b(?:testing|chaos|experiment(?:ing)?)\s+(?:in|on)\s+prod(?:uction)?\b",
            re.IGNORECASE,
        ),
        0.40,
        "Financial red flag: testing in production on live systems",
    ),
    (
        re.compile(
            r"\b(?:auto[- ]merge|autonomous merge|automatic merge)\s+without\s+(?:human|review|oversight|approval)\b",
            re.IGNORECASE,
        ),
        0.35,
        "Financial red flag: bypass of accountable human review",
    ),
]

# Credibility indicators: (compiled_regex, credit_weight, description)
CREDIBILITY_RULES: list[tuple[re.Pattern[str], float, str]] = [
    (
        re.compile(
            r"\b(?:empirical (?:evaluation|study|analysis|results)|controlled experiment)\b",
            re.IGNORECASE,
        ),
        0.20,
        "Empirical study and controlled experiment",
    ),
    (
        re.compile(
            r"\b(?:mutation score|mutation testing|mutant killed|mutation analysis)\b",
            re.IGNORECASE,
        ),
        0.20,
        "Mutation testing effectiveness metrics",
    ),
    (
        re.compile(
            r"\b(?:ablation study|ablation analysis)\b",
            re.IGNORECASE,
        ),
        0.15,
        "Ablation study validation",
    ),
    (
        re.compile(
            r"\b(?:false positive rate|false negative rate|f1[- ]score|precision and recall|precision/recall)\b",
            re.IGNORECASE,
        ),
        0.15,
        "Statistical verification and error bounds",
    ),
    (
        re.compile(
            r"\b(?:statistically significant|p[- ]value|confidence interval)\b",
            re.IGNORECASE,
        ),
        0.15,
        "Statistical significance reporting",
    ),
    (
        re.compile(
            r"\b(?:ground truth|benchmark dataset|reproducibility package|replication package|open[- ]source repo)\b",
            re.IGNORECASE,
        ),
        0.15,
        "Reproducible benchmark or open dataset",
    ),
    (
        re.compile(
            r"\b(?:production post[- ]mortem|chaos engineering|fault injection|automated canary)\b",
            re.IGNORECASE,
        ),
        0.20,
        "Production verification or chaos testing",
    ),
    (
        re.compile(
            r"\b(?:formal verification|property[- ]based testing|symbolic execution|smt solver)\b",
            re.IGNORECASE,
        ),
        0.20,
        "Formal verification and property testing",
    ),
    # Evidence of Adequacy & Governance (Ref: ADR-0021)
    (
        re.compile(
            r"\b(?:evidence of adequacy|proof of testing|calibrated confidence score|change impact analysis|blast[- ]radius)\b",
            re.IGNORECASE,
        ),
        0.20,
        "Evidence of adequacy and change risk quantification",
    ),
]

# Domain relevance indicators for Dual-Track classification (Ref: ADR-0021)
DOMAIN_RELEVANCE_RULES: list[tuple[re.Pattern[str], float, str]] = [
    (
        re.compile(
            r"\b(?:"
            # Test paradigms & execution
            r"mutation\s+testing|property[- ]based(?:\s+testing|\s+fuzzing)?|differential\s+fuzzing|"
            r"flaky\s+tests?|predictive\s+test\s+selection|automated\s+program\s+repair|"
            r"test\s+(?:synthesis|generation|runner|execution|optimization|minimization|selection)|"
            r"end[- ]to[- ]end\s+testing|e2e\s+testing|contract\s+testing|canary\s+analysis|"
            r"chaos\s+engineering|fault\s+injection|failure\s+injection|"
            r"fault\s+localization|concolic\s+execution|"
            # Test types & frameworks
            r"(?:unit|integration|regression|e2e|smoke|system|acceptance)\s+tests?|"
            r"software\s+testing|automated\s+testing|test\s+suites?|"
            r"pytest|junit|playwright|selenium|cypress|vitest|fuzz(?:bench|er|ing)?|"
            r"assertions?|mocking|sandboxing"
            r")\b",
            re.IGNORECASE,
        ),
        0.45,
        "Software Testing (Deterministic) anchor",
    ),
    (
        re.compile(
            r"\b(?:"
            r"llm\s+evals?|llm[- ]as[- ]a[- ]judge|prompt\s+regression|hallucination\s+detection|"
            r"agent\s+benchmarking|behavioral\s+drift|prompt\s+injection|jailbreak\s+defense|"
            r"adversarial\s+red[- ]teaming|eval(?:uation)?\s+harness(?:es)?|"
            r"evaluating\s+(?:large\s+language\s+models|llms?|agents?)|swe[- ]bench|model\s+evaluation"
            r")\b",
            re.IGNORECASE,
        ),
        0.45,
        "AI Evaluation (Non-Deterministic) anchor",
    ),
    (
        re.compile(
            r"\b(?:"
            r"mutation\s+score|evidence\s+of\s+adequacy|proof\s+of\s+testing|confidence\s+score|"
            r"change\s+impact|blast[- ]radius|risk\s+of\s+change|coverage\s+analysis|"
            r"branch\s+coverage|code\s+coverage|formal\s+verification|invariant\s+synthesis"
            r")\b",
            re.IGNORECASE,
        ),
        0.35,
        "Adequacy evidence and confidence proof",
    ),
    (
        re.compile(
            r"\b(?:"
            r"ci/cd|pipeline|runner|compiler|codebase|repository|pull\s+requests?|git\s+commits?|"
            r"hermetic|monorepo|ast\s+parsing|distributed\s+systems?|microservices?|headless\s+browsers?"
            r")\b",
            re.IGNORECASE,
        ),
        0.25,
        "Software engineering operational context",
    ),
]


class NoiseSieve:
    """Stage 1 rule-based classifier evaluating marketing noise, financial red flags, and domain relevance (Ref: ADR-0021)."""

    def __init__(
        self,
        drop_threshold: float = 0.60,
        base_noise: float = 0.20,
        relevance_threshold: float = 0.35,
    ) -> None:
        self.drop_threshold = drop_threshold
        self.base_noise = base_noise
        self.relevance_threshold = relevance_threshold

    def evaluate(
        self, payload: SourcePayload, authority_weight: float = 1.0
    ) -> tuple[NoiseFilterResult, QualifiedSignal | None]:
        """Evaluate a raw SourcePayload against heuristic rules.

        Returns:
            A tuple of (NoiseFilterResult, QualifiedSignal | None). If the noise score
            is <= drop_threshold and domain relevance >= relevance_threshold,
            QualifiedSignal is populated; otherwise it is None.
        """
        combined_text = f"{payload.title} {payload.raw_content}"

        matched_hype: list[str] = []
        matched_financial_red_flags: list[str] = []
        hype_penalty = 0.0
        for pattern, weight, desc in HYPE_RULES:
            if pattern.search(combined_text):
                matched_hype.append(desc)
                if "Financial red flag" in desc:
                    matched_financial_red_flags.append(desc)
                hype_penalty += weight

        matched_credibility: list[str] = []
        credibility_credit = 0.0
        for pattern, weight, desc in CREDIBILITY_RULES:
            if pattern.search(combined_text):
                matched_credibility.append(desc)
                credibility_credit += weight

        # Domain relevance scoring
        matched_relevance: list[str] = []
        relevance_points = 0.0
        for pattern, weight, desc in DOMAIN_RELEVANCE_RULES:
            if pattern.search(combined_text):
                matched_relevance.append(desc)
                relevance_points += weight

        domain_relevance_score = round(min(1.0, relevance_points), 2)

        # Authority discount: dampens noise for verified academic/enterprise sources
        authority_discount = max(0.0, (authority_weight - 1.0) * 0.20)

        # Final clamped noise score
        raw_score = self.base_noise + hype_penalty - credibility_credit - authority_discount
        noise_score = round(max(0.0, min(1.0, raw_score)), 2)

        has_red_flags = len(matched_financial_red_flags) > 0
        is_low_noise = (noise_score <= self.drop_threshold) and not has_red_flags
        is_relevant = domain_relevance_score >= self.relevance_threshold
        passed = is_low_noise and is_relevant

        rejection_reasons: list[str] = []
        if has_red_flags:
            for flag in matched_financial_red_flags:
                rejection_reasons.append(f"Financial enterprise red flag triggered: {flag}")

        if not is_low_noise and not has_red_flags:
            for desc in matched_hype:
                rejection_reasons.append(f"Exceeded hype threshold: {desc}")
            if not rejection_reasons:
                rejection_reasons.append(
                    f"Heuristic noise score {noise_score:.2f} exceeded threshold {self.drop_threshold:.2f}"
                )

        if not is_relevant:
            rejection_reasons.append(
                f"Insufficient domain relevance ({domain_relevance_score:.2f} < {self.relevance_threshold:.2f}): "
                "lacks software testing or AI evaluation indicators"
            )

        filter_result = NoiseFilterResult(
            payload_id=payload.id,
            passed=passed,
            noise_score=noise_score,
            domain_relevance_score=domain_relevance_score,
            matched_hype_indicators=matched_hype,
            matched_credibility_indicators=matched_credibility,
            matched_relevance_indicators=matched_relevance,
            matched_financial_red_flags=matched_financial_red_flags,
            rejection_reasons=rejection_reasons,
        )

        qualified_signal: QualifiedSignal | None = None
        if passed:
            qualified_signal = QualifiedSignal(
                payload=payload,
                noise_score=noise_score,
                quality_markers=matched_credibility,
            )

        return filter_result, qualified_signal

    def filter_batch(
        self, payloads: list[SourcePayload], authority_weight: float = 1.0
    ) -> tuple[list[QualifiedSignal], list[NoiseFilterResult]]:
        """Filter a batch of raw payloads, separating qualified signals from audit drops."""
        qualified: list[QualifiedSignal] = []
        audit: list[NoiseFilterResult] = []

        for p in payloads:
            res, qual = self.evaluate(p, authority_weight=authority_weight)
            audit.append(res)
            if qual is not None:
                qualified.append(qual)

        return qualified, audit
