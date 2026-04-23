from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AIProviderResult:
    source_mode: str
    confidence: float
    provider: str
    degraded: bool


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


class LLMClient:
    DEFAULT_TIMEOUT = 60.0
    MAX_RETRIES = 2

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.DEFAULT_TIMEOUT,
        )

    def chat(
        self,
        messages: list[ChatMessage | dict],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [msg if isinstance(msg, dict) else {"role": msg.role, "content": msg.content} for msg in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "reasoning_disable": True,
        }
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = self._client.post("/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                if not content and msg.get("reasoning"):
                    content = msg["reasoning"]
                logger.info(f"[LLM raw] finish={data['choices'][0].get('finish_reason')} content_len={len(content)} content={content[:200]}")
                return content
            except (httpx.HTTPStatusError, httpx.TimeoutException, KeyError) as exc:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {exc}")
                if attempt == self.MAX_RETRIES:
                    raise
                time.sleep(1)
        return ""

    def close(self):
        self._client.close()


class MarketplaceAIProvider:
    def __init__(self):
        self.settings = get_settings()
        self._llm: LLMClient | None = None
        self._init_llm()

    def _init_llm(self):
        provider = (self.settings.ai_provider or "mock").strip().lower() or "mock"
        if provider in {"mock", "rule", "rules"}:
            return
        if not self.settings.ai_api_key:
            return
        try:
            self._llm = LLMClient(
                api_key=self.settings.ai_api_key,
                base_url=self.settings.ai_base_url or "https://api.openai.com/v1",
                model=self.settings.ai_model or "qwen3.5-plus",
            )
        except Exception as exc:
            logger.warning(f"Failed to initialize LLM client: {exc}")

    def status(self) -> AIProviderResult:
        provider = (self.settings.ai_provider or "mock").strip().lower() or "mock"
        has_live_config = provider not in {"mock", "rule", "rules"} and bool(self.settings.ai_api_key)
        if has_live_config and self._llm is not None:
            return AIProviderResult(
                source_mode="provider",
                confidence=0.82,
                provider=f"qwen3.5-plus",
                degraded=False,
            )
        return AIProviderResult(
            source_mode="rules",
            confidence=0.46,
            provider=provider,
            degraded=True,
        )

    def chat(self, messages: list[ChatMessage | dict], max_tokens: int = 512, temperature: float = 0.7) -> str:
        if self._llm is None:
            raise RuntimeError("LLM client not initialized. Check AI_API_KEY and AI_BASE_URL configuration.")
        return self._llm.chat(messages, max_tokens=max_tokens, temperature=temperature)

    def structured_chat(self, messages: list[ChatMessage | dict], schema: dict, max_tokens: int = 1024) -> dict[str, Any]:
        if self._llm is None:
            raise RuntimeError("LLM client not initialized. Check AI_API_KEY and AI_BASE_URL configuration.")
        system_msg = {
            "role": "system",
            "content": (
                "You are a JSON-only assistant for a Chinese second-hand marketplace. "
                "Your ONLY job is to output valid JSON matching the user's requested schema. "
                "CRITICAL RULES:\n"
                "1. Output ONLY a single JSON object, nothing else (no text, no markdown, no explanation)\n"
                "2. The JSON must contain exactly these keys: " + ", ".join(schema.keys()) + "\n"
                "3. String values should be in Chinese\n"
                "4. Array values should have 3 items max\n"
                "5. No markdown fences, no backticks, no code blocks\n"
                "6. Always output valid JSON - if unsure, output minimal valid JSON\n"
                f"Schema: {json.dumps(schema, ensure_ascii=False)}"
            ),
        }
        all_messages = [system_msg] + [msg if isinstance(msg, dict) else {"role": msg.role, "content": msg.content} for msg in messages]
        raw = self._llm.chat(all_messages, max_tokens=max_tokens, temperature=0.3)
        raw = raw.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) >= 3:
                raw = parts[1]
                if raw.startswith("json"):
                    raw = raw[4:]
        logger.info(f"[AI raw response] {raw[:300]}")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raw = raw.strip()
            brace_start = raw.find("{")
            if brace_start != -1:
                raw = raw[brace_start:]
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                if not raw.strip().startswith("{"):
                    logger.error(f"LLM returned non-JSON response (likely reasoning/thinking): {raw[:200]}")
                    raise ValueError(f"LLM response is not valid JSON: {raw[:200]}")
                return {"_raw": raw}
