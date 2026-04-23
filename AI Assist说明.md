# AI Assist 功能说明

## 概述

AI Assist 是校园集市平台的智能助手模块，为用户提供商品发布和内容审核的 AI 辅助能力。采用 **LLM + 规则双轨制** 设计，优先调用真实 LLM，失败时自动降级到规则引擎。

---

## 核心代码架构

### 1. AI 提供者 (ai_provider.py)

**文件位置**: `backend/app/core/ai_provider.py`

#### 数据类定义

```11:22:backend/app/core/ai_provider.py
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
```

#### LLM 客户端封装

```31:80:backend/app/core/ai_provider.py
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
                logger.info(f"[LLM raw] finish={data['choices'][0].get('finish_reason')} content_len={len(content)}")
                return content
            except (httpx.HTTPStatusError, httpx.TimeoutException, KeyError) as exc:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {exc}")
                if attempt == self.MAX_RETRIES:
                    raise
                time.sleep(1)
        return ""
```

#### MarketplaceAIProvider 主类

```83:129:backend/app/core/ai_provider.py
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
```

#### 结构化输出方法

```126:167:backend/app/core/ai_provider.py
    def structured_chat(self, messages: list[ChatMessage | dict], schema: dict, max_tokens: int = 1024) -> dict[str, Any]:
        if self._llm is None:
            raise RuntimeError("LLM client not initialized.")
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
            # 尝试提取 JSON 部分
            raw = raw.strip()
            brace_start = raw.find("{")
            if brace_start != -1:
                raw = raw[brace_start:]
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                logger.error(f"LLM returned non-JSON response: {raw[:200]}")
                raise ValueError(f"LLM response is not valid JSON: {raw[:200]}")
```

---

### 2. AI 服务层 (intelligence.py)

**文件位置**: `backend/app/services/intelligence.py`

#### 服务初始化

```35:43:backend/app/services/intelligence.py
class IntelligenceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IntelligenceRepository(db)
        self.catalog_repo = CatalogRepository(db)
        self.trade_repo = TradeRepository(db)
        self.search = SearchIndexService(db)
        self.dispatcher = TaskDispatcher()
        self.ai_provider = MarketplaceAIProvider()
```

#### AI 元数据封装

```50:57:backend/app/services/intelligence.py
    def _ai_meta(self, confidence: float | None = None) -> dict:
        status = self.ai_provider.status()
        return {
            "source_mode": status.source_mode,
            "confidence": round(confidence if confidence is not None else status.confidence, 2),
            "provider": status.provider,
            "degraded": status.degraded,
        }
```

#### 发布草稿生成 (ai_listing_copilot)

```459:515:backend/app/services/intelligence.py
    def ai_listing_copilot(self, payload: dict) -> dict:
        keywords = [str(item).strip() for item in payload.get("keywords", []) if str(item).strip()]
        category = str(payload.get("category") or "闲置").strip()
        condition = str(payload.get("condition") or "成色良好").strip()
        selling_points = [str(item).strip() for item in payload.get("selling_points", []) if str(item).strip()]
        images = payload.get("images", []) or []

        try:
            schema = {
                "title": "string (商品标题, 12-30字)",
                "description": "string (商品描述, 80-200字, 包含成色、配件、交易方式)",
                "highlights": ["array of 3 strings (核心卖点)"],
                "pricing_hint": "string (定价参考建议, 20-50字)",
                "deal_tips": ["array of 3 strings (交易注意事项)"],
            }
            user_content = (
                f"为一个{category}类闲置商品生成发布文案。\n"
                f"关键词：{', '.join(keywords) if keywords else '无'}\n"
                f"成色：{condition}\n"
                f"卖点：{', '.join(selling_points) if selling_points else '无'}\n"
                f"图片数量：{len(images)}张\n"
                f"请生成标题、描述、卖点、定价参考和交易提示。"
            )
            result_data = self.ai_provider.structured_chat(
                [LLMMessage(role="user", content=user_content)],
                schema=schema,
                max_tokens=2000,
            )
            result = {
                "title": result_data.get("title", f"{category}闲置转让"),
                "description": result_data.get("description", ""),
                "highlights": result_data.get("highlights", []),
                "pricing_hint": result_data.get("pricing_hint", "建议参考同类成交价定价。"),
                "deal_tips": result_data.get("deal_tips", ["优先面交验货", "确认配件完整度", "写清交付方式"]),
                **self._ai_meta(0.82),  # LLM 成功：confidence = 0.82
            }
        except Exception as exc:
            logger.warning(f"ai_listing_copilot LLM call failed, falling back: {exc}")
            # 降级到规则生成
            title_tokens = [token for token in [category, condition, *(keywords[:2] or selling_points[:2])] if token]
            highlights = (selling_points[:3] or keywords[:3])[:3]
            description_parts = [
                f"适合想找{category}类闲置、同时希望信息透明的买家。",
                f"当前建议突出 {condition}、配件情况和实际交付方式。",
            ]
            if highlights:
                description_parts.append(f"重点可写：{'、'.join(highlights)}。")
            if images:
                description_parts.append("已检测到图片素材，建议补一段实拍图与瑕疵说明，提升信任感。")
            result = {
                "title": " / ".join(title_tokens[:3])[:36] or f"{category}闲置转让",
                "description": " ".join(description_parts),
                "highlights": highlights,
                "pricing_hint": "建议结合同类成交价、成色与配件完整度定价。",
                "deal_tips": ["优先写清验货方式", "说明是否支持邮寄/面交", "列出瑕疵和缺失配件"],
                **self._ai_meta(0.67),  # 规则降级：confidence = 0.67
            }
        return result
```

#### 内容风险审核 (ai_moderation_preview)

```414:446:backend/app/services/intelligence.py
    def ai_moderation_preview(self, title: str, description: str):
        try:
            schema = {
                "risk_level": "string (HIGH | MEDIUM | LOW, 内容违规风险等级)",
                "flags": ["array of strings (具体违规关键词或风险点, 0-5条)"],
            }
            user_content = (
                f"请审查以下二手商品发布内容，判断是否含有违规风险。\n"
                f"标题：{title}\n"
                f"描述：{description}\n"
                f"请输出风险等级（HIGH/MEDIUM/LOW）和具体风险点列表。"
            )
            result_data = self.ai_provider.structured_chat(
                [LLMMessage(role="user", content=user_content)],
                schema=schema,
                max_tokens=2000,
            )
            result = {
                "risk_level": result_data.get("risk_level", "LOW"),
                "flags": result_data.get("flags", []),
                **self._ai_meta(0.82),  # LLM 成功：confidence = 0.82
            }
        except Exception as exc:
            logger.warning(f"ai_moderation_preview LLM call failed, falling back: {exc}")
            risk = "LOW" if "违禁" not in f"{title}{description}" else "HIGH"
            result = {
                "risk_level": risk,
                "flags": [] if risk == "LOW" else ["SENSITIVE_TERM"],
                **self._ai_meta(0.58 if risk == "LOW" else 0.72),  # 规则降级
            }
        self.repo.log_ai_task("moderation_preview", title, result)
        self.db.commit()
        return result
```

---

### 3. 前端界面 (PublishProduct.vue)

**文件位置**: `frontend/src/views/user/PublishProduct.vue`

#### AI 元数据计算

```349:363:frontend/src/views/user/PublishProduct.vue
const aiMeta = computed(() => {
  if (!aiResult.value?.confidence) return null
  const mode = aiResult.value.source_mode || aiResult.value.provider || 'unknown'
  const confidence = aiResult.value.confidence
  const degraded = aiResult.value.degraded
  return { mode, confidence, degraded, realAi: confidence >= 0.8 }
})

const moderationMeta = computed(() => {
  if (!moderation.value?.confidence) return null
  const mode = moderation.value.source_mode || moderation.value.provider || 'unknown'
  const confidence = moderation.value.confidence
  const degraded = moderation.value.degraded
  return { mode, confidence, degraded, realAi: confidence >= 0.8 }
})
```

#### 徽章显示模板

```ai-source-badge 显示逻辑:
<span v-if="aiMeta.realAi">AI 生成</span>
<span v-else>规则生成</span>
<span class="ai-source-detail">{{ aiMeta.mode }} · {{ (aiMeta.confidence * 100).toFixed(0) }}%</span>
```

---

## 双轨制流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    用户点击「生成草稿」                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            LLMClient.structured_chat() 调用                  │
│                     ↓                                       │
│         API Key 配置正确?                                    │
│         网络可用?                                           │
│         LLM 服务正常?                                        │
└─────────────────────────────────────────────────────────────┘
                │                    │
              成功                  失败
                │                    │
                ▼                    ▼
┌────────────────────┐    ┌────────────────────────────────┐
│ confidence = 0.82  │    │  降级到规则引擎                  │
│ source_mode =      │    │  confidence = 0.67             │
│   "provider"       │    │  source_mode = "rules"         │
└────────────────────┘    └────────────────────────────────┘
                │                    │
                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    前端徽章显示                               │
│  confidence ≥ 0.8 → 🟢「AI 生成」                           │
│  confidence < 0.8 → ⚪「规则生成」                          │
└─────────────────────────────────────────────────────────────┘
```

---

## confidence 判断标准

| confidence 值 | 徽章 | 来源 | 说明 |
|---------------|------|------|------|
| `0.82` | 🟢 AI 生成 | `**self._ai_meta(0.82)` | LLM 调用成功 |
| `0.67` | ⚪ 规则生成 | `**self._ai_meta(0.67)` | `ai_listing_copilot` 降级 |
| `0.58` | ⚪ 规则生成 | `**self._ai_meta(0.58)` | `ai_moderation_preview` 降级（低风险） |
| `0.72` | ⚪ 规则生成 | `**self._ai_meta(0.72)` | `ai_moderation_preview` 降级（高风险） |

前端判断：

```javascript
const realAi = confidence >= 0.8  // true → AI 生成，false → 规则生成
```

---

## 配置项

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `AI_PROVIDER` | AI 提供商 | `mock` |
| `AI_API_KEY` | API 密钥 | 空 |
| `AI_BASE_URL` | API 地址 | 空 |
| `AI_MODEL` | 模型名称 | `qwen3.5-plus` |

---

## API 接口

### 生成发布草稿

```
POST /api/ai/products/draft
```

请求体：
```json
{
  "category": "数码",
  "keywords": ["MacBook", "轻薄"],
  "condition": "95新",
  "selling_points": ["原装配件", "无划痕"]
}
```

成功响应 (LLM)：
```json
{
  "title": "MacBook Air M2 95新 轻薄便携",
  "description": "这是一台...（AI生成的完整描述）",
  "highlights": ["轻薄便携", "性能强劲", "电池耐用"],
  "pricing_hint": "建议参考同型号成交价，在2000-2500元区间",
  "deal_tips": ["优先面交验货", "确认配件完整度", "写清交付方式"],
  "source_mode": "provider",
  "confidence": 0.82,
  "provider": "qwen3.5-plus",
  "degraded": false
}
```

降级响应 (规则)：
```json
{
  "title": "数码 / 95新 / MacBook",
  "description": "适合想找数码类闲置...",
  "highlights": ["MacBook", "轻薄", "原装配件"],
  "source_mode": "rules",
  "confidence": 0.67,
  "provider": "mock",
  "degraded": true
}
```

### 内容风险审核

```
POST /api/ai/moderation/preview
```

请求体：
```json
{
  "title": "商品标题",
  "description": "商品描述"
}
```

响应：
```json
{
  "risk_level": "LOW",
  "flags": [],
  "source_mode": "provider",
  "confidence": 0.82,
  "degraded": false
}
```

---

## 相关文件清单

| 文件 | 作用 |
|------|------|
| `backend/app/core/ai_provider.py` | LLM 客户端封装、结构化输出、配置读取 |
| `backend/app/services/intelligence.py` | AI 服务层、业务逻辑、降级处理 |
| `backend/app/core/config.py` | 配置管理（AI_PROVIDER 等） |
| `frontend/src/views/user/PublishProduct.vue` | 发布页面、AI Assist 面板、徽章显示 |
