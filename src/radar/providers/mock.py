"""Deterministic Mock LLM Provider for unit and offline tests."""

import inspect
import math
from enum import Enum
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from radar.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class MockProvider(LLMProvider):
    """Deterministic offline mock provider."""

    def __init__(self, embedding_dim: int = 1536) -> None:
        self.embedding_dim = embedding_dim

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        _ = system_prompt
        return f"[MOCK RESPONSE] Analysis for: {prompt[:40]}..."

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        """Instantiate response model with dummy valid values for testing."""
        _ = system_prompt
        fields = response_model.model_fields
        dummy_data: dict[str, Any] = {}
        prompt_lower = prompt.lower()

        # Context-aware defaults if prompt contains structured sections
        extracted_name = "Mock Data"
        if "Title: " in prompt:
            raw_title = prompt.split("Title: ")[1].split("\n")[0].strip()
            if raw_title:
                extracted_name = raw_title[:60]

        extracted_body = ""
        if "Content Body / Abstract:" in prompt:
            body_part = prompt.split("Content Body / Abstract:")[1].strip()
            first_line = body_part.split("\n")[0].strip()
            if first_line:
                extracted_body = first_line[:150]

        if response_model.__name__ == "SynthesizedTopic":
            from radar.core.models import QECategory

            if any(
                k in prompt_lower
                for k in ("mutation", "mutant", "pitest", "stryker", "infection", "mull")
            ):
                name_val = "Automated Mutation Testing & Fault Injection"
                summary_val = (
                    "Automated mutation synthesis and execution engines verifying test suite "
                    "adequacy across language runtimes."
                )
                cat_val = QECategory.EXECUTION_AND_OPTIMIZATION
            elif any(
                k in prompt_lower
                for k in (
                    "browser",
                    "mcp",
                    "agent",
                    "lightpanda",
                    "checkquest",
                    "qaia",
                    "xhimatty",
                    "tagmanager",
                    "orangepro",
                )
            ):
                name_val = "Autonomous Browser & UI Agent Systems"
                summary_val = (
                    "Autonomous browser-driving agents and local execution runtimes for end-to-end "
                    "UI verification."
                )
                cat_val = QECategory.AGENT_SYSTEMS
            elif any(
                k in prompt_lower
                for k in ("pensive", "diagnosis", "failure", "sapienz", "heal", "rca")
            ):
                name_val = "Automated Failure Diagnosis & Self-Healing"
                summary_val = (
                    "Production-grade root cause analysis and automated test repair for flaky and "
                    "failing test executions."
                )
                cat_val = QECategory.TRIAGE_AND_FIX
            elif any(k in prompt_lower for k in ("blast", "radius", "api", "quasar", "ads event")):
                name_val = "API Change Impact & Blast Radius Analysis"
                summary_val = (
                    "Static and dynamic dependency graph analysis measuring consumer blast radius for "
                    "library and API changes."
                )
                cat_val = QECategory.TEST_SYNTHESIS
            elif any(
                k in prompt_lower for k in ("flowstep", "trajectory", "predict", "github action")
            ):
                name_val = "Predictive CI/CD & Trajectory Optimization"
                summary_val = (
                    "Machine learning architectures predicting CI pipeline execution and optimizing "
                    "agentic trajectories."
                )
                cat_val = QECategory.TEST_SYNTHESIS
            elif any(k in prompt_lower for k in ("redteam", "aigoat", "security", "banking")):
                name_val = "LLM Red-Teaming & Security Verification"
                summary_val = (
                    "Adversarial evaluation frameworks and security vulnerability testbeds for "
                    "enterprise LLM applications."
                )
                cat_val = QECategory.GOVERNANCE_AND_EVALS
            else:
                name_val = "Emerging AI Test Architecture"
                summary_val = "Emerging paradigms in automated software quality engineering."
                cat_val = QECategory.SPEC_AND_MODEL

            return response_model.model_validate(
                {
                    "name": name_val,
                    "summary": summary_val,
                    "primary_category": cat_val,
                }
            )

        for name, field_info in fields.items():
            ann = field_info.annotation
            annotation_str = str(ann)

            if ann is not None and inspect.isclass(ann) and issubclass(ann, Enum):
                enum_cls = ann
                if enum_cls.__name__ == "TrackType":
                    from radar.core.models import TrackType

                    if any(
                        k in prompt_lower
                        for k in (
                            "evaluation",
                            "evals",
                            "red-team",
                            "red team",
                            "drift",
                            "hallucination",
                            "judge",
                            "agent",
                        )
                    ):
                        dummy_data[name] = TrackType.EVALUATION
                    else:
                        dummy_data[name] = TrackType.TESTING
                elif enum_cls.__name__ == "QECategory":
                    from radar.core.models import QECategory

                    if any(
                        k in prompt_lower
                        for k in (
                            "mutation",
                            "mutant",
                            "pitest",
                            "mutmut",
                            "stryker",
                            "infection",
                        )
                    ):
                        dummy_data[name] = QECategory.EXECUTION_AND_OPTIMIZATION
                    elif any(
                        k in prompt_lower
                        for k in ("property", "fuzz", "spec", "synthesis", "keploy")
                    ):
                        dummy_data[name] = QECategory.TEST_SYNTHESIS
                    elif any(
                        k in prompt_lower
                        for k in (
                            "redteam",
                            "red-team",
                            "eval",
                            "security",
                            "goat",
                            "governance",
                        )
                    ):
                        dummy_data[name] = QECategory.GOVERNANCE_AND_EVALS
                    elif any(
                        k in prompt_lower
                        for k in ("flaky", "heal", "diagnosis", "repair", "pensive")
                    ):
                        dummy_data[name] = QECategory.TRIAGE_AND_FIX
                    elif any(k in prompt_lower for k in ("agent", "autonomous", "mcp")):
                        dummy_data[name] = QECategory.AGENT_SYSTEMS
                    else:
                        dummy_data[name] = QECategory.SPEC_AND_MODEL
                elif enum_cls.__name__ == "EvidenceTier":
                    from radar.core.models import EvidenceTier

                    if "arxiv" in prompt_lower:
                        dummy_data[name] = EvidenceTier.ACADEMIC_PEER_REVIEWED
                    elif "github.com" in prompt_lower:
                        dummy_data[name] = EvidenceTier.OPEN_SOURCE_REPO
                    elif any(
                        k in prompt_lower
                        for k in (
                            "netflix",
                            "uber",
                            "engineering.fb",
                            "post-mortem",
                            "blog",
                        )
                    ):
                        dummy_data[name] = EvidenceTier.ENGINEERING_POST_MORTEM
                    else:
                        dummy_data[name] = EvidenceTier.VENDOR_ANNOUNCEMENT
                else:
                    dummy_data[name] = list(enum_cls)[0]
            elif "float" in annotation_str:
                if response_model.__name__ == "CommitteeAuditResult":
                    if (
                        "wrapper=true" in prompt_lower
                        or "is_superficial_wrapper: true" in prompt_lower
                        or "hype product" in prompt_lower
                        or "vanity" in prompt_lower
                    ):
                        dummy_data[name] = 0.30
                    elif any(
                        k in prompt_lower
                        for k in (
                            "stryker",
                            "pitest",
                            "mutant",
                            "keploy",
                            "sapienz",
                            "pensive",
                            "automut",
                        )
                    ):
                        if name == "security_score":
                            dummy_data[name] = 0.88
                        elif name == "cicd_score":
                            dummy_data[name] = 0.84
                        else:
                            dummy_data[name] = 0.90
                    elif any(
                        k in prompt_lower
                        for k in (
                            "flowstep",
                            "trajectory",
                            "pytagmanager",
                            "orangepro",
                            "lightpanda",
                            "spec-property",
                            "rca-tracer",
                        )
                    ):
                        if name == "security_score":
                            dummy_data[name] = 0.76
                        elif name == "cicd_score":
                            dummy_data[name] = 0.72
                        else:
                            dummy_data[name] = 0.78
                    elif any(
                        k in prompt_lower
                        for k in (
                            "xhimatty",
                            "checkquest",
                            "redteam",
                            "aigoat",
                            "qaia",
                            "hyperbolic",
                            "infection",
                            "mutmut",
                            "mull",
                        )
                    ):
                        if name == "security_score":
                            dummy_data[name] = 0.65
                        elif name == "cicd_score":
                            dummy_data[name] = 0.60
                        else:
                            dummy_data[name] = 0.65
                    else:
                        dummy_data[name] = 0.75
                else:
                    dummy_data[name] = 0.75
            elif "int" in annotation_str:
                dummy_data[name] = 1
            elif "list" in annotation_str:
                if name == "technical_claims":
                    dummy_data[name] = [
                        "Verifiable automated test assertion",
                        "Continuous CI integration",
                    ]
                elif name == "adequacy_evidence":
                    dummy_data[name] = ["mutation score verification"]
                else:
                    dummy_data[name] = []
            elif "str" in annotation_str:
                if name == "name":
                    dummy_data[name] = extracted_name
                elif name == "key_innovation":
                    dummy_data[name] = extracted_body or "Automated quality engineering capability."
                elif name == "topic_name":
                    dummy_data[name] = extracted_name
                elif name == "summary":
                    dummy_data[name] = extracted_body or "Synthesized topic summary."
                else:
                    dummy_data[name] = "Mock Data"
            elif "bool" in annotation_str:
                if name == "is_superficial_wrapper":
                    dummy_data[name] = "wrapper" in prompt_lower or "hype" in prompt_lower
                elif name == "is_qe_relevant":
                    dummy_data[name] = True
                elif name == "has_open_source_repo":
                    dummy_data[name] = "github.com" in prompt_lower
                elif name == "has_reproducible_benchmark":
                    dummy_data[name] = any(
                        k in prompt_lower
                        for k in ("benchmark", "evaluation", "evals", "dataset", "arxiv")
                    )
                else:
                    dummy_data[name] = True
            elif "UUID" in annotation_str:
                dummy_data[name] = uuid4()
            else:
                pass
        return response_model.model_validate(dummy_data)

    async def embed_text(self, text: str) -> list[float]:
        """Generate deterministic unit vector biased by semantic theme keywords for clustering."""
        text_lower = text.lower()

        # Identify thematic cluster seed for mock convergence
        theme_seed: int | None = None
        if any(
            k in text_lower
            for k in (
                "mutation",
                "mutant",
                "pitest",
                "stryker",
                "infection",
                "mull",
                "mutmut",
                "automut",
            )
        ):
            theme_seed = 1010101
        elif any(
            k in text_lower
            for k in (
                "browser",
                "mcp",
                "agent",
                "lightpanda",
                "checkquest",
                "qaia",
                "xhimatty",
                "tagmanager",
                "orangepro",
                "playwright",
                "puppeteer",
            )
        ):
            theme_seed = 2020202
        elif any(
            k in text_lower
            for k in (
                "pensive",
                "diagnosis",
                "failure",
                "sapienz",
                "heal",
                "rca",
                "root cause",
                "flaky",
            )
        ):
            theme_seed = 3030303
        elif any(
            k in text_lower
            for k in (
                "blast",
                "radius",
                "api",
                "quasar",
                "ads event",
                "dependency graph",
                "impact",
            )
        ):
            theme_seed = 4040404
        elif any(
            k in text_lower
            for k in (
                "flowstep",
                "trajectory",
                "predict",
                "github action",
                "pipeline",
            )
        ):
            theme_seed = 5050505
        elif any(
            k in text_lower
            for k in (
                "redteam",
                "aigoat",
                "security",
                "banking",
                "adversarial",
                "jailbreak",
            )
        ):
            theme_seed = 6060606

        import hashlib
        import random

        # Fully deterministic 64-bit seed from text
        text_seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
        ind_rng = random.Random(text_seed)
        ind_vec = [ind_rng.gauss(0, 1) for _ in range(self.embedding_dim)]

        if theme_seed is not None:
            theme_rng = random.Random(theme_seed)
            theme_base = [theme_rng.gauss(0, 1) for _ in range(self.embedding_dim)]
            t_norm = math.sqrt(sum(x * x for x in theme_base))
            if t_norm > 0:
                theme_base = [x / t_norm for x in theme_base]
            i_norm = math.sqrt(sum(x * x for x in ind_vec))
            if i_norm > 0:
                ind_vec = [x / i_norm for x in ind_vec]
            # 85% theme base + 15% individual variation -> cosine similarity ~0.97 within theme
            combined = [0.85 * tb + 0.15 * iv for tb, iv in zip(theme_base, ind_vec, strict=False)]
        else:
            combined = ind_vec

        norm = math.sqrt(sum(x * x for x in combined))
        if norm > 0.0:
            combined = [x / norm for x in combined]
        return combined
