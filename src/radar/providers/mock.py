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
        """Generate deterministic pseudo-orthogonal unit vector based on text hash."""
        seed = abs(hash(text))
        vec = [
            (float((seed * (i + 1) * 2654435761) % 1000) / 1000.0) - 0.5
            for i in range(self.embedding_dim)
        ]
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [x / norm for x in vec]
        return vec
