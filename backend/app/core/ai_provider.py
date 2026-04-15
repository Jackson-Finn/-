from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(slots=True)
class AIProviderResult:
    source_mode: str
    confidence: float
    provider: str
    degraded: bool


class MarketplaceAIProvider:
    def __init__(self):
        self.settings = get_settings()

    def status(self) -> AIProviderResult:
        provider = (self.settings.ai_provider or "mock").strip().lower() or "mock"
        has_live_config = provider not in {"mock", "rule", "rules"} and bool(self.settings.ai_api_key)
        if has_live_config:
            return AIProviderResult(
                source_mode="provider",
                confidence=0.78,
                provider=provider,
                degraded=False,
            )
        return AIProviderResult(
            source_mode="rules",
            confidence=0.46,
            provider=provider,
            degraded=True,
        )
