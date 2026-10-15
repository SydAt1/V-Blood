"""
External LLM Interpretation Provider (Milestone 6).

Adapter for commercial and local LLM endpoints (OpenAI, Anthropic, Ollama, vLLM)
with structured JSON generation and post-execution guardrail verification.
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import Any

from dotenv import load_dotenv

from vblood.interpretation.guardrails import GroundingGuardrail
from vblood.interpretation.providers.base import InterpretationProvider
from vblood.interpretation.schemas import (
    CohortInterpretationResponse,
    PlaygroundInterpretationResponse,
)

load_dotenv()

SYSTEM_PROMPT = """You are an expert computational biologist and red blood cell physiologist interpreting mechanistic simulation results for the V-Blood platform.

Core constraints:
1. Ground all numbers strictly in the provided simulation metrics. Never invent or hallucinate nadirs, peak peroxide concentrations, or recovery times.
2. Erythrocytes lack nuclei and mitochondria. Survival depends entirely on the pentose phosphate pathway (generating NADPH) and the glutathione redox cycle.
3. V-Blood simulates isolated erythrocytes in an in vitro aqueous suspension. Do NOT claim in vivo pharmacokinetics (ADME), renal clearance, or hepatic metabolism.
4. Output your analysis strictly as a valid JSON object matching the requested schema.
"""


def _clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


class ExternalLLMProvider(InterpretationProvider):
    """Client adapter for external LLM endpoints (Gemini, OpenAI, Anthropic, Ollama, vLLM)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        vblood_key = os.environ.get("VBLOOD_LLM_API_KEY")
        explicit_base = base_url or os.environ.get("LLM_BASE_URL")
        explicit_model = model or os.environ.get("LLM_MODEL")

        # Prioritize valid API keys (Gemini first if provided/requested)
        if api_key:
            self.api_key = api_key
            self.base_url = (explicit_base or "https://api.openai.com/v1").rstrip("/")
            self.model = explicit_model or "gpt-4o-mini"
        elif self._is_valid_key(gemini_key):
            self.api_key = gemini_key
            self.base_url = (
                explicit_base or "https://generativelanguage.googleapis.com/v1beta/openai"
            ).rstrip("/")
            self.model = explicit_model or "gemini-2.5-flash"
        elif self._is_valid_key(openai_key):
            self.api_key = openai_key
            self.base_url = (explicit_base or "https://api.openai.com/v1").rstrip("/")
            self.model = explicit_model or "gpt-4o-mini"
        elif self._is_valid_key(anthropic_key):
            self.api_key = anthropic_key
            self.base_url = (explicit_base or "https://api.openai.com/v1").rstrip("/")
            self.model = explicit_model or "claude-3-5-sonnet-20241022"
        else:
            # Fallback when placeholder or unset
            self.api_key = gemini_key or openai_key or anthropic_key or vblood_key
            if gemini_key and "gemini" in gemini_key.lower():
                self.base_url = (
                    explicit_base or "https://generativelanguage.googleapis.com/v1beta/openai"
                ).rstrip("/")
                self.model = explicit_model or "gemini-2.5-flash"
            else:
                self.base_url = (explicit_base or "https://api.openai.com/v1").rstrip("/")
                self.model = explicit_model or "gpt-4o-mini"

        self.guardrail = GroundingGuardrail()

    @staticmethod
    def _is_valid_key(key: str | None) -> bool:
        if not key or not key.strip():
            return False
        k = key.strip()
        return not (k.startswith("your_") or k in ("REPLACE_ME", "sk-...", "sk-ant-...", "AIzaSy..."))

    @property
    def provider_id(self) -> str:
        return f"external-llm:{self.model}"

    def is_available(self) -> bool:
        """Returns True if a valid API key or local custom base_url is configured."""
        if self._is_valid_key(self.api_key):
            return True
        # Local model endpoint (e.g. localhost:11434 or 127.0.0.1:8000) might not need an API key
        if self.base_url and ("localhost" in self.base_url or "127.0.0.1" in self.base_url):
            return True
        return False

    def _call_gemini_native(self, user_content: str) -> dict[str, Any]:
        """Execute synchronous HTTP request to the native Gemini REST endpoint."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_content}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
            },
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidate = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(_clean_json_text(candidate))

    def _call_chat_completion(self, user_content: str) -> dict[str, Any]:
        """Execute synchronous HTTP request to the LLM chat completions endpoint with automatic Gemini fallback."""
        if not self.is_available():
            raise RuntimeError("External LLM provider is not configured (missing API key or endpoint).")

        # Native Gemini endpoint route
        if "generativelanguage.googleapis.com" in self.base_url and "/openai" not in self.base_url:
            return self._call_gemini_native(user_content)

        # Standard OpenAI-compatible endpoint route (supported by OpenAI, Gemini /v1beta/openai, Ollama, etc.)
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or 'none'}",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return json.loads(_clean_json_text(content))
        except Exception as exc:
            # If using Google's OpenAI layer and it encounters an error, fallback to native Gemini REST endpoint
            if "generativelanguage.googleapis.com" in self.base_url and self.api_key:
                try:
                    return self._call_gemini_native(user_content)
                except Exception as gemini_exc:
                    raise RuntimeError(f"Gemini API invocation failed: {gemini_exc}") from gemini_exc
            raise RuntimeError(f"External LLM invocation failed: {exc}") from exc

    async def interpret_playground(
        self,
        context: dict[str, Any],
    ) -> PlaygroundInterpretationResponse:
        """Invoke external LLM to generate single-cell interpretation."""
        user_prompt = (
            f"Please interpret the following single-cell erythrocyte simulation scenario and return a JSON object with keys: "
            f"'executive_summary', 'nadir_analysis', 'pathway_flux_breakdown', 'control_comparison', "
            f"'uncertainty_and_limitations', 'suggested_experiments' (list of strings).\n\n"
            f"Simulation Context:\n{json.dumps(context, indent=2)}"
        )
        parsed = self._call_chat_completion(user_prompt)

        dummy_resp = PlaygroundInterpretationResponse.model_construct(
            executive_summary=parsed.get("executive_summary", ""),
            nadir_analysis=parsed.get("nadir_analysis", ""),
            pathway_flux_breakdown=parsed.get("pathway_flux_breakdown", ""),
            control_comparison=parsed.get("control_comparison", ""),
            uncertainty_and_limitations=parsed.get("uncertainty_and_limitations", ""),
            suggested_experiments=parsed.get("suggested_experiments", []),
            provider_used=self.provider_id,
            grounding=None,  # type: ignore
        )
        grounding = self.guardrail.verify_playground(dummy_resp, context)

        return PlaygroundInterpretationResponse(
            executive_summary=parsed.get("executive_summary", ""),
            nadir_analysis=parsed.get("nadir_analysis", ""),
            pathway_flux_breakdown=parsed.get("pathway_flux_breakdown", ""),
            control_comparison=parsed.get("control_comparison", ""),
            uncertainty_and_limitations=parsed.get("uncertainty_and_limitations", ""),
            suggested_experiments=parsed.get("suggested_experiments", []),
            provider_used=self.provider_id,
            fallback_applied=False,
            fallback_reason=None,
            grounding=grounding,
        )

    async def interpret_cohort(
        self,
        context: dict[str, Any],
    ) -> CohortInterpretationResponse:
        """Invoke external LLM to generate cohort interpretation."""
        user_prompt = (
            f"Please interpret the following heterogeneous erythrocyte cohort simulation and return a JSON object with keys: "
            f"'executive_summary', 'tail_risk_analysis', 'g6pd_interaction_analysis', 'lysis_risk_evaluation', "
            f"'uncertainty_and_limitations', 'suggested_experiments' (list of strings).\n\n"
            f"Cohort Context:\n{json.dumps(context, indent=2)}"
        )
        parsed = self._call_chat_completion(user_prompt)

        dummy_resp = CohortInterpretationResponse.model_construct(
            executive_summary=parsed.get("executive_summary", ""),
            tail_risk_analysis=parsed.get("tail_risk_analysis", ""),
            g6pd_interaction_analysis=parsed.get("g6pd_interaction_analysis", ""),
            lysis_risk_evaluation=parsed.get("lysis_risk_evaluation", ""),
            uncertainty_and_limitations=parsed.get("uncertainty_and_limitations", ""),
            suggested_experiments=parsed.get("suggested_experiments", []),
            provider_used=self.provider_id,
            grounding=None,  # type: ignore
        )
        grounding = self.guardrail.verify_cohort(dummy_resp, context)

        return CohortInterpretationResponse(
            executive_summary=parsed.get("executive_summary", ""),
            tail_risk_analysis=parsed.get("tail_risk_analysis", ""),
            g6pd_interaction_analysis=parsed.get("g6pd_interaction_analysis", ""),
            lysis_risk_evaluation=parsed.get("lysis_risk_evaluation", ""),
            uncertainty_and_limitations=parsed.get("uncertainty_and_limitations", ""),
            suggested_experiments=parsed.get("suggested_experiments", []),
            provider_used=self.provider_id,
            fallback_applied=False,
            fallback_reason=None,
            grounding=grounding,
        )
