"""Thin client for the Moonshot / Kimi OpenAI-compatible API."""

from __future__ import annotations

import os
import re
from typing import Optional

from openai import AsyncOpenAI, OpenAIError


class KimiServiceError(Exception):
    """Raised when the Kimi/Moonshot service cannot complete a request."""


class KimiService:
    """Call the Kimi/Moonshot chat API and parse the markdown response."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        request_timeout: float = 60.0,
        max_code_chars: int = 32000,
    ) -> None:
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        self.base_url = base_url or os.getenv(
            "KIMI_BASE_URL", "https://api.moonshot.cn/v1"
        )
        self.model = model or os.getenv("KIMI_MODEL", "kimi-latest")
        self.request_timeout = request_timeout
        self.max_code_chars = max_code_chars

        # Allow the server to boot and serve the UI without a key, but fail
        # clearly when the composer endpoint is used.
        self._client: Optional[AsyncOpenAI] = None
        if self.api_key:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.request_timeout,
            )

    @property
    def configured(self) -> bool:
        return self._client is not None

    async def compose(
        self,
        code: str,
        instruction: str,
        language: str = "python",
    ) -> dict[str, str]:
        """Ask Kimi to rewrite *code* according to *instruction*.

        Returns a dict with:
            - explanation: free-form text before the code block.
            - code: the extracted updated code, or the original code if none was found.
            - language: the language identifier passed in.
        """
        if not self._client:
            raise KimiServiceError("KIMI_API_KEY is not configured")

        instruction = (instruction or "").strip()
        if not instruction:
            raise KimiServiceError("Instruction prompt cannot be empty")

        code = code or ""
        if len(code) > self.max_code_chars:
            raise KimiServiceError(
                f"Code payload exceeds the limit of {self.max_code_chars} characters"
            )

        system_prompt = (
            "You are a helpful coding tutor powered by Kimi/Moonshot. "
            "The user provides source code and an instruction. "
            "Briefly explain the changes you plan to make, then provide the "
            "complete updated code in a single fenced markdown code block. "
            "If no changes are needed, say so and return the original code unchanged."
        )

        user_prompt = (
            f"Language: {language}\n\n"
            f"Original code:\n```{language}\n{code}\n```\n\n"
            f"Instruction: {instruction}\n\n"
            "Please respond with a short explanation followed by the updated code block."
        )

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except OpenAIError as exc:
            raise KimiServiceError(f"Kimi API error: {exc}") from exc

        content = response.choices[0].message.content or ""
        return self._parse_response(content, fallback_code=code, language=language)

    @staticmethod
    def _parse_response(
        content: str,
        fallback_code: str,
        language: str,
    ) -> dict[str, str]:
        """Extract explanation and the last fenced code block from the model output.

        Using the last block is defensive: if the model echoes the original code
        first and then the updated code, we prefer the update.
        """
        content = content.strip()
        if not content:
            return {
                "explanation": "The model returned an empty response.",
                "code": fallback_code,
                "language": language,
            }

        # Match ``` optionally followed by a language tag, then any text until ```.
        code_block_re = re.compile(r"```(?:[^\n]*)\n(.*?)```", re.DOTALL)
        blocks = code_block_re.findall(content)

        if blocks:
            # Take the last code block to avoid picking up example snippets.
            code = blocks[-1].strip()
            # Remove all fenced blocks so the explanation only contains prose.
            explanation = code_block_re.sub("", content).strip()
            return {
                "explanation": explanation,
                "code": code,
                "language": language,
            }

        # No fenced block: treat the whole response as the explanation and keep code.
        return {
            "explanation": content,
            "code": fallback_code,
            "language": language,
        }
