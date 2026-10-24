"""Shared utilities for LLM provider adapters."""

import json
import re

from pydantic import BaseModel, ValidationError

from radar.core.exceptions import ProviderError


def extract_json_payload(raw_text: str) -> str:
    """Extract clean JSON string from raw model text, stripping markdown code fences."""
    cleaned = raw_text.strip()
    # Check for ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if match:
        return match.group(1).strip()
    return cleaned


def parse_and_validate[T: BaseModel](raw_text: str, model_cls: type[T]) -> T:
    """Parse JSON string and validate against a target Pydantic model."""
    extracted = extract_json_payload(raw_text)
    try:
        return model_cls.model_validate_json(extracted)
    except (ValidationError, ValueError) as err:
        # Try loading raw dict first to provide cleaner error message
        try:
            data = json.loads(extracted)
            if isinstance(data, dict):
                return model_cls.model_validate(data)
        except Exception:
            pass
        raise ProviderError(
            f"Failed to validate response against {model_cls.__name__}: {err}\nRaw text: {raw_text[:200]}"
        ) from err


def build_schema_prompt[T: BaseModel](
    prompt: str, model_cls: type[T], system_prompt: str | None = None
) -> tuple[str, str]:
    """Construct prompt and system instruction containing explicit Pydantic JSON schema."""
    schema_json = json.dumps(model_cls.model_json_schema(), indent=2)
    schema_instruction = (
        f"You must respond ONLY with a valid JSON object strictly matching this JSON schema:\n"
        f"{schema_json}\n"
        f"Do not include any conversational preamble, commentary, or markdown wrapping outside the JSON."
    )

    full_system = (
        f"{system_prompt}\n\n{schema_instruction}" if system_prompt else schema_instruction
    )
    return prompt, full_system
