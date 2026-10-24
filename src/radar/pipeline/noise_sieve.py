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
        0.15,
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
]


class NoiseSieve:
    """Stage 1 rule-based classifier evaluating marketing noise and technical credibility."""

    def __init__(
        self,
        drop_threshold: float = 0.60,
        base_noise: float = 0.20,
    ) -> None:
        self.drop_threshold = drop_threshold
        self.base_noise = base_noise

    def evaluate(
        self, payload: SourcePayload, authority_weight: float = 1.0
    ) -> tuple[NoiseFilterResult, QualifiedSignal | None]:
        """Evaluate a raw SourcePayload against heuristic rules.

        Returns:
            A tuple of (NoiseFilterResult, QualifiedSignal | None). If the noise score
            is <= drop_threshold, QualifiedSignal is populated; otherwise it is None.
        """
        combined_text = f"{payload.title} {payload.raw_content}"

        matched_hype: list[str] = []
        hype_penalty = 0.0
        for pattern, weight, desc in HYPE_RULES:
            if pattern.search(combined_text):
                matched_hype.append(desc)
                hype_penalty += weight

        matched_credibility: list[str] = []
        credibility_credit = 0.0
        for pattern, weight, desc in CREDIBILITY_RULES:
            if pattern.search(combined_text):
                matched_credibility.append(desc)
                credibility_credit += weight

        # Authority discount: dampens noise for verified academic/enterprise sources
        authority_discount = max(0.0, (authority_weight - 1.0) * 0.20)

        # Final clamped score
        raw_score = self.base_noise + hype_penalty - credibility_credit - authority_discount
        noise_score = round(max(0.0, min(1.0, raw_score)), 2)

        passed = noise_score <= self.drop_threshold

        rejection_reasons: list[str] = []
        if not passed:
            for desc in matched_hype:
                rejection_reasons.append(f"Exceeded hype threshold: {desc}")
            if not rejection_reasons:
                rejection_reasons.append(
                    f"Heuristic noise score {noise_score:.2f} exceeded threshold {self.drop_threshold:.2f}"
                )

        filter_result = NoiseFilterResult(
            payload_id=payload.id,
            passed=passed,
            noise_score=noise_score,
            matched_hype_indicators=matched_hype,
            matched_credibility_indicators=matched_credibility,
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
