"""
Interpretation Orchestration Service (Milestone 6).

Coordinates prompt context assembly, provider selection ('auto', 'deterministic', 'llm'),
automatic fallback on external failure, and guardrail verification.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Literal

from vblood.interpretation.context import (
    UNMODELED_PHYSICS_CATALOGUE,
    _get_val,
    build_cohort_context,
    build_playground_context,
)
from vblood.interpretation.providers.deterministic import DeterministicBiochemicalProvider
from vblood.interpretation.providers.llm_client import ExternalLLMProvider
from vblood.interpretation.schemas import (
    CohortInterpretationRequest,
    CohortInterpretationResponse,
    InterpretationStatusResponse,
    PlaygroundInterpretationRequest,
    PlaygroundInterpretationResponse,
)

logger = logging.getLogger(__name__)


class InterpretationService:
    """Service orchestrating scientific interpretation requests with caching."""

    def __init__(
        self,
        deterministic_provider: DeterministicBiochemicalProvider | None = None,
        llm_provider: ExternalLLMProvider | None = None,
    ) -> None:
        self.deterministic_provider = deterministic_provider or DeterministicBiochemicalProvider()
        self.llm_provider = llm_provider or ExternalLLMProvider()
        self._memory_cache: dict[str, Any] = {}
        self._cache_dir = Path(os.environ.get("VBLOOD_ARTIFACT_DIR", "./simulation_outputs")) / "interpretations"
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _get_cached_playground(self, key: str) -> PlaygroundInterpretationResponse | None:
        """Retrieve cached playground memorandum from memory or disk."""
        if key in self._memory_cache:
            return self._memory_cache[key]
        disk_path = self._cache_dir / f"{key.replace(':', '_')}.json"
        if disk_path.exists():
            try:
                data = json.loads(disk_path.read_text(encoding="utf-8"))
                resp = PlaygroundInterpretationResponse.model_validate(data)
                self._memory_cache[key] = resp
                return resp
            except Exception as exc:
                logger.debug(f"Cache miss or read failure for {key}: {exc}")
        return None

    def _save_cached_playground(self, key: str, resp: PlaygroundInterpretationResponse) -> None:
        """Store playground memorandum in memory and disk cache."""
        self._memory_cache[key] = resp
        disk_path = self._cache_dir / f"{key.replace(':', '_')}.json"
        try:
            disk_path.write_text(resp.model_dump_json(indent=2), encoding="utf-8")
        except Exception as exc:
            logger.debug(f"Failed to persist cache file for {key}: {exc}")

    def _get_cached_cohort(self, key: str) -> CohortInterpretationResponse | None:
        """Retrieve cached cohort memorandum from memory or disk."""
        if key in self._memory_cache:
            return self._memory_cache[key]
        disk_path = self._cache_dir / f"{key.replace(':', '_')}.json"
        if disk_path.exists():
            try:
                data = json.loads(disk_path.read_text(encoding="utf-8"))
                resp = CohortInterpretationResponse.model_validate(data)
                self._memory_cache[key] = resp
                return resp
            except Exception as exc:
                logger.debug(f"Cache miss or read failure for {key}: {exc}")
        return None

    def _save_cached_cohort(self, key: str, resp: CohortInterpretationResponse) -> None:
        """Store cohort memorandum in memory and disk cache."""
        self._memory_cache[key] = resp
        disk_path = self._cache_dir / f"{key.replace(':', '_')}.json"
        try:
            disk_path.write_text(resp.model_dump_json(indent=2), encoding="utf-8")
        except Exception as exc:
            logger.debug(f"Failed to persist cache file for {key}: {exc}")

    def get_status(self) -> InterpretationStatusResponse:
        """Inspect provider readiness and guardrail status."""
        llm_avail = self.llm_provider.is_available()
        providers = ["deterministic"]
        if llm_avail:
            providers.append("llm")

        return InterpretationStatusResponse(
            providers_available=providers,
            default_provider="llm" if llm_avail else "deterministic",
            llm_configured=llm_avail,
            llm_model=self.llm_provider.model if llm_avail else None,
            guardrails_active=True,
            unmodeled_physics_declared=UNMODELED_PHYSICS_CATALOGUE,
        )

    async def interpret_playground(
        self,
        request: PlaygroundInterpretationRequest,
    ) -> PlaygroundInterpretationResponse:
        """Process and interpret a single-cell playground scenario run."""
        context = build_playground_context(
            request=request.scenario_request,
            result=request.scenario_result,
            control_result=request.control_result,
        )

        preference = request.provider_preference
        raw_run_id = _get_val(request.scenario_result, "run_id")
        if not raw_run_id:
            h = hashlib.sha256(json.dumps(context.get("endpoints", {}), sort_keys=True).encode()).hexdigest()[:16]
            raw_run_id = f"ctx_{h}"

        # 1. Check cache if not forcing refresh
        if not request.force_refresh:
            if preference == "deterministic":
                cached = self._get_cached_playground(f"playground:{raw_run_id}:deterministic")
                if cached:
                    logger.info(f"Returning cached deterministic interpretation for {raw_run_id}")
                    return cached
            elif preference == "llm":
                cached = self._get_cached_playground(f"playground:{raw_run_id}:llm")
                if cached:
                    logger.info(f"Returning cached LLM interpretation for {raw_run_id}")
                    return cached
            elif preference == "auto":
                # Prefer cached LLM if available, then auto, then deterministic
                cached_llm = self._get_cached_playground(f"playground:{raw_run_id}:llm")
                if cached_llm:
                    return cached_llm
                cached_auto = self._get_cached_playground(f"playground:{raw_run_id}:auto")
                if cached_auto:
                    return cached_auto
                if not self.llm_provider.is_available():
                    cached_det = self._get_cached_playground(f"playground:{raw_run_id}:deterministic")
                    if cached_det:
                        return cached_det

        # 2. Execution & Generation
        use_llm = preference == "llm" or (preference == "auto" and self.llm_provider.is_available())

        if use_llm:
            try:
                logger.info(f"Invoking external LLM provider ({self.llm_provider.provider_id}) for run {raw_run_id}.")
                resp = await self.llm_provider.interpret_playground(context)
                self._save_cached_playground(f"playground:{raw_run_id}:llm", resp)
                self._save_cached_playground(f"playground:{raw_run_id}:auto", resp)
                return resp
            except Exception as exc:
                if preference == "llm":
                    raise RuntimeError(f"Requested LLM provider failed: {exc}") from exc
                logger.warning(f"LLM provider failed; falling back to deterministic engine: {exc}")
                resp = await self.deterministic_provider.interpret_playground(context)
                resp = resp.model_copy(update={
                    "fallback_applied": True,
                    "fallback_reason": str(exc),
                })
                self._save_cached_playground(f"playground:{raw_run_id}:auto", resp)
                return resp

        # Deterministic engine
        resp = await self.deterministic_provider.interpret_playground(context)
        self._save_cached_playground(f"playground:{raw_run_id}:deterministic", resp)
        if preference == "auto":
            self._save_cached_playground(f"playground:{raw_run_id}:auto", resp)
        return resp

    async def interpret_cohort(
        self,
        request: CohortInterpretationRequest,
    ) -> CohortInterpretationResponse:
        """Process and interpret a heterogeneous cohort simulation experiment."""
        context = build_cohort_context(
            request=request.population_request,
            result=request.population_result,
        )

        preference = request.provider_preference
        raw_run_id = _get_val(request.population_result, "run_id")
        if not raw_run_id:
            h = hashlib.sha256(json.dumps(context.get("distribution_endpoints", {}), sort_keys=True).encode()).hexdigest()[:16]
            raw_run_id = f"cohort_{h}"

        # 1. Check cache if not forcing refresh
        if not request.force_refresh:
            if preference == "deterministic":
                cached = self._get_cached_cohort(f"cohort:{raw_run_id}:deterministic")
                if cached:
                    logger.info(f"Returning cached deterministic cohort interpretation for {raw_run_id}")
                    return cached
            elif preference == "llm":
                cached = self._get_cached_cohort(f"cohort:{raw_run_id}:llm")
                if cached:
                    logger.info(f"Returning cached LLM cohort interpretation for {raw_run_id}")
                    return cached
            elif preference == "auto":
                cached_llm = self._get_cached_cohort(f"cohort:{raw_run_id}:llm")
                if cached_llm:
                    return cached_llm
                cached_auto = self._get_cached_cohort(f"cohort:{raw_run_id}:auto")
                if cached_auto:
                    return cached_auto
                if not self.llm_provider.is_available():
                    cached_det = self._get_cached_cohort(f"cohort:{raw_run_id}:deterministic")
                    if cached_det:
                        return cached_det

        # 2. Execution & Generation
        use_llm = preference == "llm" or (preference == "auto" and self.llm_provider.is_available())

        if use_llm:
            try:
                logger.info(f"Invoking external LLM provider for cohort {raw_run_id}.")
                resp = await self.llm_provider.interpret_cohort(context)
                self._save_cached_cohort(f"cohort:{raw_run_id}:llm", resp)
                self._save_cached_cohort(f"cohort:{raw_run_id}:auto", resp)
                return resp
            except Exception as exc:
                if preference == "llm":
                    raise RuntimeError(f"Requested LLM provider failed: {exc}") from exc
                logger.warning(f"LLM cohort interpretation failed; falling back to deterministic engine: {exc}")
                resp = await self.deterministic_provider.interpret_cohort(context)
                resp = resp.model_copy(update={
                    "fallback_applied": True,
                    "fallback_reason": str(exc),
                })
                self._save_cached_cohort(f"cohort:{raw_run_id}:auto", resp)
                return resp

        resp = await self.deterministic_provider.interpret_cohort(context)
        self._save_cached_cohort(f"cohort:{raw_run_id}:deterministic", resp)
        if preference == "auto":
            self._save_cached_cohort(f"cohort:{raw_run_id}:auto", resp)
        return resp


_GLOBAL_SERVICE: InterpretationService | None = None


def get_interpretation_service() -> InterpretationService:
    """Return the global InterpretationService singleton."""
    global _GLOBAL_SERVICE
    if _GLOBAL_SERVICE is None:
        _GLOBAL_SERVICE = InterpretationService()
    return _GLOBAL_SERVICE
