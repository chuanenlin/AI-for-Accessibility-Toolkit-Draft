"""LLM client for agent reasoning.

Supports Anthropic, OpenAI, and Google as providers.
Used by agents when LLM-powered reasoning is enabled.
"""

from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "google"

DEFAULTS = {
    "google": "gemini-2.5-flash",
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
}

ENV_KEYS = {
    "google": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


class LLMClient:
    """Multi-provider LLM client for agent reasoning.

    Args:
        provider: "anthropic", "openai", or "google".
        model: Model name. Defaults per provider if not set.
        api_key: API key. Falls back to environment variable.

    Example:
        llm = LLMClient()  # Google Gemini 2.5 Flash (default)
        llm = LLMClient(provider="anthropic")
        llm = LLMClient(provider="openai", model="gpt-4o")
    """

    def __init__(
        self,
        provider: str = DEFAULT_PROVIDER,
        model: str | None = None,
        api_key: str | None = None,
    ):
        if provider not in DEFAULTS:
            raise ValueError(f"Unknown provider: {provider!r}. Use: {', '.join(DEFAULTS)}")
        self.provider = provider
        self.model = model or DEFAULTS[provider]
        self.api_key = api_key or os.environ.get(ENV_KEYS[provider], "")

    def complete(self, system: str, prompt: str) -> str:
        """Get a text completion from the LLM.

        Args:
            system: System prompt (role/instructions).
            prompt: User prompt (the question/task).

        Returns:
            The LLM's response text.
        """
        if self.provider == "anthropic":
            return self._complete_anthropic(system, prompt)
        elif self.provider == "openai":
            return self._complete_openai(system, prompt)
        elif self.provider == "google":
            return self._complete_google(system, prompt)
        raise ValueError(f"Unknown provider: {self.provider}")

    def complete_json(self, system: str, prompt: str) -> dict:
        """Get a JSON completion from the LLM.

        Instructs the model to respond with valid JSON and parses the result.
        """
        result = self.complete(
            system + "\n\nRespond with valid JSON only. No markdown fences, no extra text.",
            prompt,
        )
        # Strip markdown code fences if the model includes them anyway
        text = result.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)

    # ── Provider implementations ────────────────────────────────────

    def _complete_anthropic(self, system: str, prompt: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key or None)
        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _complete_openai(self, system: str, prompt: str) -> str:
        import openai

        client = openai.OpenAI(api_key=self.api_key or None)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    def _complete_google(self, system: str, prompt: str) -> str:
        from google import genai

        client = genai.Client(api_key=self.api_key or None)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system,
            ),
        )
        return response.text

    def __repr__(self) -> str:
        return f"<LLMClient provider={self.provider!r} model={self.model!r}>"
