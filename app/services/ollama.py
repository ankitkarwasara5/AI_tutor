from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class OllamaService:
    """Ollama adapter with separate connection and generation timeouts."""

    def __init__(
        self,
        *,
        base_url: str,
        connect_timeout_seconds: int,
        generation_timeout_seconds: int,
        preferred_models: tuple[str, ...],
        disabled: bool = False,
    ):
        self.base_url = base_url
        self.connect_timeout_seconds = connect_timeout_seconds
        self.generation_timeout_seconds = generation_timeout_seconds
        self.preferred_models = preferred_models
        self.disabled = disabled
        self.client: Any | None = None
        self.selected_model: str | None = None
        self._warmed_up = False
        self.available_models: list[str] = []
        self.last_error: str | None = None
        self.last_generation_error: str | None = None
        self._last_connect_attempt = 0.0
        self._connect_lock = asyncio.Lock()

    @property
    def available(self) -> bool:
        return self.client is not None and self.selected_model is not None

    async def initialize(self, *, force: bool = False) -> None:
        if self.disabled:
            self.last_error = "Ollama integration disabled by configuration"
            logger.info(self.last_error)
            return

        now = time.monotonic()
        if not force and now - self._last_connect_attempt < 3.0:
            return

        async with self._connect_lock:
            now = time.monotonic()
            if not force and now - self._last_connect_attempt < 3.0:
                return
            self._last_connect_attempt = now

            try:
                import ollama  # type: ignore
            except ImportError:
                self.last_error = "Ollama Python package is not installed"
                logger.info("%s; using offline fallback mode", self.last_error)
                return

            try:
                # Important: the HTTP client's timeout must be long enough for
                # generation. Connectivity itself is bounded separately below.
                try:
                    self.client = ollama.Client(
                        host=self.base_url,
                        timeout=self.generation_timeout_seconds,
                    )
                except TypeError:
                    self.client = ollama.Client(host=self.base_url)

                response = await asyncio.wait_for(
                    asyncio.to_thread(self.client.list),
                    timeout=max(self.connect_timeout_seconds, 1),
                )
                models = self._extract_model_names(response)
                self.available_models = models
                self.selected_model = self._select_model(models)
                self.last_error = None
                self._warmed_up = False
                if self.selected_model:
                    logger.info("Selected Ollama model: %s", self.selected_model)
                else:
                    self.last_error = (
                        "Ollama is reachable but no local models were found"
                    )
                    logger.info("%s", self.last_error)
            except Exception as exc:
                self.last_error = self._describe_error(exc)
                logger.warning("Ollama unavailable; using fallback mode: %s", exc)
                self.client = None
                self.selected_model = None
                self.available_models = []

    async def ensure_available(self, *, force: bool = False) -> bool:
        if self.available:
            return True
        await self.initialize(force=force)
        return self.available

    def _extract_model_names(self, response: Any) -> list[str]:
        if isinstance(response, dict):
            raw_models = response.get("models", [])
        else:
            raw_models = getattr(response, "models", [])

        names: list[str] = []
        for model in raw_models:
            if isinstance(model, dict):
                name = model.get("model") or model.get("name")
            else:
                name = getattr(model, "model", None) or getattr(model, "name", None)
            if name:
                names.append(str(name))
        return names

    def _select_model(self, available_models: list[str]) -> str | None:
        for preferred in self.preferred_models:
            if preferred in available_models:
                return preferred
        return available_models[0] if available_models else None

    def _supports_thinking_control(self) -> bool:
        model = (self.selected_model or "").lower()
        return "qwen3" in model or "deepseek" in model

    async def warm_up(self) -> None:
        if not self.available or self._warmed_up:
            return
        try:
            await self.chat(
                "Reply with OK.",
                num_predict=8,
                temperature=0.0,
                system_prompt="Respond briefly and accurately.",
                think=False,
            )
            self._warmed_up = True
        except Exception as exc:
            logger.debug("Ollama warm-up failed: %s", exc)

    async def chat(
        self,
        prompt: str,
        *,
        num_predict: int,
        temperature: float,
        system_prompt: str | None = None,
        format_schema: dict[str, Any] | str | None = None,
        think: bool | None = None,
    ) -> str:
        if not self.available or self.client is None or self.selected_model is None:
            raise RuntimeError("Ollama is not available")

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self.selected_model,
            "messages": messages,
            "options": {
                "num_predict": num_predict,
                "temperature": temperature,
            },
        }
        if format_schema is not None:
            kwargs["format"] = format_schema

        # Qwen3 thinking is useful interactively, but for schema-constrained
        # application output it adds latency and can make parsing less predictable.
        if think is not None and self._supports_thinking_control():
            kwargs["think"] = think

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(self.client.chat, **kwargs),
                timeout=max(self.generation_timeout_seconds, 1),
            )
            if isinstance(response, dict):
                content = str(response["message"]["content"]).strip()
            else:
                content = str(response.message.content).strip()
            if not content:
                raise RuntimeError("Ollama returned an empty response")
            self.last_generation_error = None
            return content
        except Exception as exc:
            self.last_generation_error = self._describe_error(exc)
            logger.warning("Ollama generation failed: %s", self.last_generation_error)
            raise

    @staticmethod
    def _describe_error(exc: Exception) -> str:
        detail = str(exc).strip()
        return f"{type(exc).__name__}: {detail}" if detail else type(exc).__name__
