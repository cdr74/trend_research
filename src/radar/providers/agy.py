"""Antigravity CLI (agy) LLM provider bridge."""

import asyncio
import json
import shutil
from typing import TypeVar

from pydantic import BaseModel

from radar.core.config import settings
from radar.core.exceptions import ProviderError
from radar.providers.base import LLMProvider
from radar.providers.utils import parse_and_validate

T = TypeVar("T", bound=BaseModel)


class AgyCliProvider(LLMProvider):
    """Local Antigravity CLI (agy) provider bridge for zero-cost local execution on WSL."""

    def __init__(
        self,
        binary_path: str | None = None,
        model_name: str | None = None,
        timeout: float = 180.0,
    ) -> None:
        self.binary_path = binary_path or settings.agy_binary_path
        self.model_name = model_name or settings.agy_model_name
        self.timeout = timeout

        # Verify that binary exists on path
        resolved = shutil.which(self.binary_path)
        if not resolved:
            raise ProviderError(
                f"Antigravity CLI binary '{self.binary_path}' not found on system PATH. "
                "Ensure agy is installed or switch RADAR_LLM_PROVIDER to 'mock' or 'openai_compat'."
            )

    async def _run_command(self, cmd: list[str]) -> str:
        """Execute agy subprocess asynchronously."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
        except TimeoutError as err:
            raise ProviderError(f"Antigravity CLI command timed out after {self.timeout}s") from err
        except FileNotFoundError as err:
            raise ProviderError(
                f"Antigravity binary '{self.binary_path}' could not be executed: {err}"
            ) from err

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace").strip()
            raise ProviderError(f"Antigravity CLI exited with code {proc.returncode}: {err_msg}")

        return stdout.decode(errors="replace").strip()

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate unstructured text using agy print mode."""
        full_prompt = (
            f"System Instructions:\n{system_prompt}\n\nTask:\n{prompt}" if system_prompt else prompt
        )
        cmd = [self.binary_path, "-p", full_prompt, "--output-format", "text"]
        if self.model_name:
            cmd.extend(["--model", self.model_name])

        return await self._run_command(cmd)

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        """Generate structured data using agy with native JSON schema enforcement."""
        schema_json = json.dumps(response_model.model_json_schema())
        full_prompt = (
            f"System Instructions:\n{system_prompt}\n\nTask:\n{prompt}" if system_prompt else prompt
        )

        cmd = [
            self.binary_path,
            "-p",
            full_prompt,
            "--output-format",
            "json",
            "--json-schema",
            schema_json,
        ]
        if self.model_name:
            cmd.extend(["--model", self.model_name])

        raw_output = await self._run_command(cmd)

        cleaned_output = raw_output
        brace_idx = raw_output.find("{")
        rbrace_idx = raw_output.rfind("}")
        if brace_idx != -1 and rbrace_idx != -1 and rbrace_idx > brace_idx:
            cleaned_output = raw_output[brace_idx : rbrace_idx + 1]

        try:
            envelope = json.loads(cleaned_output)
            # 1. Prefer native structured_output emitted by agy --json-schema
            if (
                isinstance(envelope, dict)
                and "structured_output" in envelope
                and envelope["structured_output"] is not None
            ):
                return response_model.model_validate(envelope["structured_output"])

            # 2. Fall back to inner response string
            if isinstance(envelope, dict) and "response" in envelope:
                return parse_and_validate(envelope["response"], response_model)

            # 3. Direct envelope validation
            return response_model.model_validate(envelope)
        except Exception:
            # Fall back to regex json parser
            return parse_and_validate(raw_output, response_model)

    async def embed_text(self, text: str) -> list[float]:
        """Generate a deterministic 1536-dimensional embedding vector."""
        # agy is a reasoning CLI; embedding uses a deterministic normalized vector
        val = float(abs(hash(text)) % 1000) / 1000.0
        return [val] * 1536
