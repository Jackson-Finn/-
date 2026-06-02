import logging
import re
from pathlib import Path

from redis import Redis
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.ai_provider import MarketplaceAIProvider, ChatMessage as LLMMessage
from app.core.config import get_settings
from app.core.storage import get_storage_service
from app.models.entities import (
    AITaskLog,
    AuditTask,
    ChatMessage,
    DomainEventRecord,
    JobRunLog,
    Order,
    Product,
    RecommendationMaterial,
    RecommendationSnapshot,
    Report,
    User,
)
from app.core.search import SearchIndexService
from app.services.task_dispatcher import TaskDispatcher
from app.repositories.catalog import CatalogRepository
from app.repositories.intelligence import IntelligenceRepository
from app.repositories.trade import TradeRepository

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class IntelligenceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IntelligenceRepository(db)
        self.catalog_repo = CatalogRepository(db)
        self.trade_repo = TradeRepository(db)
        self.search = SearchIndexService(db)
        self.dispatcher = TaskDispatcher()
        self.ai_provider = MarketplaceAIProvider()

    @staticmethod
    def _format_error(exc: Exception) -> str:
        message = str(exc).strip().splitlines()[0] if str(exc).strip() else exc.__class__.__name__
        return f"{exc.__class__.__name__}: {message}"[:180]

    def _ai_meta(self, confidence: float | None = None) -> dict:
        status = self.ai_provider.status()
        return {
            "source_mode": status.source_mode,
            "confidence": round(confidence if confidence is not None else status.confidence, 2),
            "provider": status.provider,
            "degraded": status.degraded,
        }

    @staticmethod
    def _check_result(
        name: str,
        label: str,
        status: str,
        mode: str,
        detail: str,
        action: str,
        critical: bool = True,
    ) -> dict:
        return {
            "name": name,
            "label": label,
            "status": status,
            "mode": mode,
            "detail": detail,
            "action": action,
            "critical": critical,
        }

    def _check_database(self) -> dict:
        try:
            self.db.execute(text("SELECT 1"))
            bind = self.db.get_bind()
            if bind is None:
                backend = "unknown"
            elif hasattr(bind, "url"):
                backend = bind.url.get_backend_name()
            elif hasattr(bind, "engine") and hasattr(bind.engine, "url"):
                backend = bind.engine.url.get_backend_name()
            else:
                backend = getattr(getattr(bind, "dialect", None), "name", "unknown")
            return self._check_result(
                "database",
                "数据库",
                "READY",
                backend.upper(),
                "主数据库连接可用，事务读写链路正常。",
                "保持当前数据库配置即可；切 MySQL 时只需要调整 DATABASE_URL。",
            )
        except Exception as exc:
            return self._check_result(
                "database",
                "数据库",
                "FAILED",
                "UNAVAILABLE",
                self._format_error(exc),
                "优先检查 DATABASE_URL、数据库文件权限或 MySQL 服务状态。",
            )

    def _check_redis(self, settings) -> dict:
        client = None
        try:
            client = Redis.from_url(
                settings.redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
                health_check_interval=0,
            )
            client.ping()
            return self._check_result(
                "redis",
                "Redis / Broker",
                "READY",
                "REDIS",
                "Redis 可访问，任务队列和缓存具备接管条件。",
                "保持 Redis 常驻；容器模式下建议通过 docker compose 启动。",
            )
        except Exception as exc:
            return self._check_result(
                "redis",
                "Redis / Broker",
                "DEGRADED",
                "OFFLINE",
                self._format_error(exc),
                "启动 Redis 后，搜索重建和推荐刷新会从同步回退切回队列模式。",
            )
        finally:
            if client is not None:
                client.close()

    def _check_async_tasks(self, redis_ready: bool) -> dict:
        if not redis_ready:
            return self._check_result(
                "async_tasks",
                "异步任务",
                "DEGRADED",
                "SYNC_FALLBACK",
                "当前无法访问 Redis，后台重建任务会以内联同步方式执行。",
                "先恢复 Redis，再启动 Celery worker：celery -A app.tasks.worker.celery_app worker --loglevel=info",
            )

        try:
            from app.tasks.worker import celery_app

            inspect = celery_app.control.inspect(timeout=1)
            stats = inspect.stats() or {}
            if stats:
                worker_names = ", ".join(sorted(stats.keys()))
                return self._check_result(
                    "async_tasks",
                    "异步任务",
                    "READY",
                    "CELERY",
                    f"已发现在线 worker：{worker_names}。",
                    "推荐继续保留独立 worker 进程处理搜索重建、推荐刷新和后续媒体任务。",
                )
            return self._check_result(
                "async_tasks",
                "异步任务",
                "DEGRADED",
                "BROKER_ONLY",
                "Redis 已可用，但没有发现在线 Celery worker，任务会回退为同步执行。",
                "启动 worker 服务，或在 compose 中确认 `worker` 容器已经 healthy。",
            )
        except Exception as exc:
            return self._check_result(
                "async_tasks",
                "异步任务",
                "DEGRADED",
                "BROKER_ONLY",
                self._format_error(exc),
                "检查 Celery worker 启动日志，确认 broker 地址和任务导入路径一致。",
            )

    def _check_storage(self, settings) -> dict:
        if settings.storage_backend == "local":
            target = Path(settings.media_storage_dir).resolve()
            try:
                target.mkdir(parents=True, exist_ok=True)
                probe = target / ".write-probe"
                probe.write_text("ok", encoding="utf-8")
                probe.unlink(missing_ok=True)
                return self._check_result(
                    "storage",
                    "媒体存储",
                    "READY",
                    "LOCAL",
                    f"本地上传目录可写：{target}",
                    "开发环境可继续使用本地目录；切容器部署时改为 MinIO 即可。",
                    critical=False,
                )
            except Exception as exc:
                return self._check_result(
                    "storage",
                    "媒体存储",
                    "FAILED",
                    "LOCAL",
                    self._format_error(exc),
                    "检查 storage 目录权限，或改用 MinIO 作为统一对象存储。",
                )

        try:
            get_storage_service().bootstrap()
            return self._check_result(
                "storage",
                "媒体存储",
                "READY",
                "MINIO",
                f"MinIO bucket `{settings.minio_bucket}` 已可访问。",
                "上传链路会自动使用对象存储，并保留后续缩略图/压缩图扩展空间。",
            )
        except Exception as exc:
            return self._check_result(
                "storage",
                "媒体存储",
                "DEGRADED",
                "MINIO",
                self._format_error(exc),
                "检查 MINIO_ENDPOINT、账号密码和 bucket 权限；必要时先切回 STORAGE_BACKEND=local。",
            )

    def _check_search(self, search_health: dict) -> dict:
        if search_health.get("available"):
            return self._check_result(
                "search",
                "搜索索引",
                "READY",
                str(search_health.get("mode", "OPENSEARCH")).upper(),
                f"索引 `{search_health.get('index')}` 可用，当前文档数 {search_health.get('document_count', 0)}。",
                "可以直接使用高级搜索、联想词和后台重建索引能力。",
            )
        return self._check_result(
            "search",
            "搜索索引",
            "DEGRADED",
            str(search_health.get("mode", "DATABASE_FALLBACK")).upper(),
            "OpenSearch 当前不可用，搜索已自动回退到数据库模式。",
            "启动 OpenSearch 后执行后台“重建搜索索引”，系统会自动恢复高级搜索能力。",
        )

    def _runbook(self) -> dict:
        return {
            "local": [
                "conda activate advanced-marketplace",
                "cd backend && uvicorn app.main:app --reload",
                "cd frontend && npm run dev",
                "cd backend && pytest -q",
            ],
            "docker": [
                "docker compose up --detach --wait --wait-timeout 300",
                "docker compose ps",
                "docker compose logs -f api worker redis minio opensearch",
                "docker compose down --remove-orphans",
            ],
            "verification": [
                "访问 /health，确认后端返回 200。",
                "登录 /admin/platform，检查数据库至少为 READY，Redis / 异步任务 / 搜索 / 存储有明确状态。",
                "执行一次“重建推荐”和“重建搜索索引”，观察作业从 PENDING 进入 COMPLETED 或显示同步回退。",
                "以卖家身份上传商品图片，确认详情页能展示 preview 图。",
            ],
            "notes": [
                "这台机器如果没有 docker 命令，平台运维台会显示依赖降级信息，但不影响本地单进程演示。",
                "Redis 不可用时，重建类任务仍然可用，只是以内联同步方式执行。",
                "OpenSearch 不可用时，搜索会回退到数据库查询，但不会阻塞商品浏览和交易主链路。",
            ],
        }

    def _product_card(self, product: Product | None) -> dict:
        if not product:
            return {}
        tags = product.tags if isinstance(product.tags, dict) else {}
        seller = self.catalog_repo.get_user(product.seller_id)
        category = self.catalog_repo.get_category(product.category_id)
        images = self.catalog_repo.list_product_images(product.id)
        return {
            "product_id": product.id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "product_status": product.product_status,
            "audit_status": product.audit_status,
            "seller_id": product.seller_id,
            "seller_name": seller.display_name if seller else None,
            "category_name": category.name if category else None,
            "cover_image": images[0].url if images else None,
            "condition_label": str(tags.get("condition_label") or tags.get("condition") or "成色良好"),
            "hero_summary": str(tags.get("hero_summary") or product.description[:72]),
            "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        }

    def _hydrate_recommendation_items(self, raw_items: list[dict]) -> list[dict]:
        items: list[dict] = []
        for item in raw_items:
            product_id = item.get("product_id") or item.get("id")
            product = self.catalog_repo.get_product(product_id) if product_id else None
            if product and product.audit_status == "APPROVED" and product.product_status == "ACTIVE":
                payload = self._product_card(product)
                payload["reason"] = item.get("reason", "Behavior-based recommendation")
                items.append(payload)
        return items

    def recommend_home(self, user_id: int | None):
        snapshot = self.repo.get_snapshot(user_id, "HOME")
        if snapshot:
            return {"items": self._hydrate_recommendation_items(snapshot.payload.get("items", []))}
        products = self.trade_repo.popular_products(limit=6)
        payload = {
            "items": [
                {
                    **self._product_card(product),
                    "reason": "Popular and recent inventory",
                }
                for product in products
            ]
        }
        self.repo.create_snapshot(RecommendationSnapshot(user_id=user_id, scene="HOME", payload=payload))
        self.db.commit()
        return payload

    def recommend_related(self, product_id: int):
        product = self.catalog_repo.get_product(product_id)
        related = [
            candidate
            for candidate in self.catalog_repo.list_products()
            if candidate.id != product_id
            and candidate.audit_status == "APPROVED"
            and candidate.product_status == "ACTIVE"
        ][:6]
        return {
            "base_product_id": product_id,
            "items": [
                {
                    **self._product_card(item),
                    "reason": f"Related to {product.title}" if product else "Marketplace similarity",
                }
                for item in related
            ],
            "reason": f"Same marketplace scene around {product.title}" if product else "Marketplace fallback recommendation",
        }

    def rebuild_recommendations(self):
        job = self.repo.log_job(
            "recommendation_rebuild",
            "PENDING",
            {"mode": "celery", "message": "Recommendation rebuild requested"},
        )
        self.db.commit()
        status, task_id = self.dispatcher.dispatch_recommendation_rebuild(job.id)
        if status == "queued":
            self.repo.update_job(
                job.id,
                "PENDING",
                {
                    **job.details,
                    "task_id": task_id,
                    "message": "Queued in Celery",
                },
            )
            self.db.commit()
        if status == "completed":
            refreshed = self.repo.get_job(job.id)
            result = refreshed.details.get("result") if refreshed else None
            return {
                "status": "completed",
                "job_id": job.id,
                "mode": "sync-fallback",
                "result": result,
            }
        return {"status": status, "job_id": job.id, "mode": "celery", "task_id": task_id}

    def reindex_search(self):
        job = self.repo.log_job(
            "search_reindex",
            "PENDING",
            {"mode": "celery", "message": "Search reindex requested"},
        )
        self.db.commit()
        status, task_id = self.dispatcher.dispatch_search_reindex(job.id)
        if status == "queued":
            self.repo.update_job(
                job.id,
                "PENDING",
                {
                    **job.details,
                    "task_id": task_id,
                    "message": "Queued in Celery",
                },
            )
            self.db.commit()
        elif status == "completed":
            refreshed = self.repo.get_job(job.id)
            result = refreshed.details.get("result") if refreshed else None
            return {
                "status": "completed",
                "job_id": job.id,
                "mode": result.get("mode", "sync-fallback") if isinstance(result, dict) else "sync-fallback",
                "result": result,
            }
        return {"status": status, "job_id": job.id, "mode": "celery", "task_id": task_id}

    def ai_product_draft(self, keywords: list[str], category: str | None):
        result = self.ai_listing_copilot(
            {
                "keywords": keywords,
                "category": category,
            }
        )
        self.repo.log_ai_task("product_draft", str({"keywords": keywords, "category": category}), result)
        self.db.commit()
        return result

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
                **self._ai_meta(0.82),
            }
        except Exception as exc:
            logger.warning(f"ai_moderation_preview LLM call failed, falling back: {exc}")
            risk = "LOW" if "违禁" not in f"{title}{description}" else "HIGH"
            result = {
                "risk_level": risk,
                "flags": [] if risk == "LOW" else ["SENSITIVE_TERM"],
                **self._ai_meta(0.58 if risk == "LOW" else 0.72),
            }
        self.repo.log_ai_task("moderation_preview", title, result)
        self.db.commit()
        return result

    def ai_chat_summary(self, session_id: int):
        result = self.ai_chat_copilot(session_id)
        summary_only = {
            "session_id": session_id,
            "summary": result["summary"],
            **self._ai_meta(result.get("confidence", 0.5)),
        }
        self.repo.log_ai_task("chat_summary", f"session:{session_id}", summary_only)
        self.db.commit()
        return summary_only

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
                **self._ai_meta(0.82),
            }
        except Exception as exc:
            logger.warning(f"ai_listing_copilot LLM call failed, falling back: {exc}")
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
                "pricing_hint": "建议结合同类成交价、成色与配件完整度做区间定价。",
                "deal_tips": ["优先写清验货方式", "说明是否支持邮寄/面交", "列出瑕疵和缺失配件"],
                **self._ai_meta(0.67),
            }
        return result

    def ai_search_assist(self, query: str) -> dict:
        raw = (query or "").strip()
        try:
            schema = {
                "keyword": "string (原始搜索词)",
                "category": "string | null (推断的品类)",
                "condition": "string | null (推断的成色要求)",
                "price_min": "int | null (最低价)",
                "price_max": "int | null (最高价)",
                "sort": "string (排序方式: newest | price_asc | price_desc)",
                "reasoning": ["array of strings (推断逻辑说明, 1-3条)"],
            }
            user_content = f"分析以下二手市场搜索词，提取结构化筛选条件：\n搜索词：{raw}\n\n请输出品类、成色、价格区间、排序等筛选条件，并说明推断理由。"
            result_data = self.ai_provider.structured_chat(
                [LLMMessage(role="user", content=user_content)],
                schema=schema,
                max_tokens=2000,
            )
            result = {
                "query": raw,
                "structured_filters": {
                    "keyword": result_data.get("keyword", raw),
                    "category": result_data.get("category"),
                    "condition": result_data.get("condition"),
                    "price_min": result_data.get("price_min"),
                    "price_max": result_data.get("price_max"),
                    "sort": result_data.get("sort", "newest"),
                },
                "search_brief": f"已把搜索意图整理成{result_data.get('category') or '通用品类'}、{result_data.get('condition') or '任意成色'}等条件。",
                "reasoning": result_data.get("reasoning", ["已提取品类、成色、价格等条件。"]),
                **self._ai_meta(0.82),
            }
        except Exception as exc:
            logger.warning(f"ai_search_assist LLM call failed, falling back: {exc}")
            normalized = raw.replace(" ", "")
            category = next((item for item in ["数码", "图书", "家居", "潮玩"] if item in normalized), None)
            condition = next((item for item in ["全新", "近新", "九成新", "95新", "99新", "正常使用"] if item in normalized), None)
            price_numbers = [int(item) for item in re.findall(r"(\d{2,6})", normalized)]
            price_min = None
            price_max = None
            if "以内" in normalized and price_numbers:
                price_max = price_numbers[0]
            elif "以上" in normalized and price_numbers:
                price_min = price_numbers[0]
            elif len(price_numbers) >= 2:
                price_min, price_max = sorted(price_numbers[:2])[:2]
            sort = "price_asc" if any(token in normalized for token in ["便宜", "低价", "性价比"]) else "newest"
            result = {
                "query": raw,
                "structured_filters": {
                    "keyword": raw,
                    "category": category,
                    "condition": condition,
                    "price_min": price_min,
                    "price_max": price_max,
                    "sort": sort,
                },
                "search_brief": f"已把搜索意图整理成{'、'.join(filter(None, [category, condition, f'{price_min}-{price_max}' if price_min or price_max else '', sort])) or '通用检索'}。",
                "reasoning": [
                    "先保留原始关键词，避免误伤长尾商品。",
                    "从类目、成色和价格词里提取可执行条件。",
                    "无法确定的条件保持为空，交给用户手动再筛。",
                ],
                **self._ai_meta(0.61),
            }
        self.repo.log_ai_task("search_assist", raw, result)
        self.db.commit()
        return result

    def ai_purchase_insights(self, product_id: int) -> dict:
        product = self.catalog_repo.get_product(product_id)
        if not product:
            return {
                "product_id": product_id,
                "summary": "当前商品不存在，无法生成购买建议。",
                "pricing_view": "无可用判断",
                "risk_level": "HIGH",
                "risk_flags": ["商品不存在或已不可见"],
                "next_questions": ["确认商品是否仍在售", "向卖家索要最新实拍图"],
                "checklist": ["确认库存", "确认交付方式"],
                **self._ai_meta(0.32),
            }
        tags = product.tags if isinstance(product.tags, dict) else {}
        reviews = self.trade_repo.list_reviews_for_product(product_id)
        deal_methods = tags.get("deal_methods") or ["邮寄", "同城面交"]
        try:
            schema = {
                "summary": "string: a 40-80 character product overview with purchase recommendation",
                "pricing_view": "string: a 20-50 character price analysis",
                "risk_level": "string: one of HIGH, MEDIUM, or LOW",
                "risk_flags": "array of 1-3 risk warning strings",
                "next_questions": "array of 2-3 questions buyer should ask the seller",
                "checklist": "array of 3-4 pre-purchase checklist items",
            }
            condition_val = tags.get("condition_label") or tags.get("condition") or "未标注"
            user_content = (
                f"为一个二手市场商品提供购买决策建议。请严格按JSON格式输出。\n"
                f"商品信息：\n"
                f"- 标题：{product.title}\n"
                f"- 描述：{product.description[:200]}\n"
                f"- 价格：{product.price}元\n"
                f"- 成色标签：{condition_val}\n"
                f"- 审核状态：{product.audit_status}\n"
                f"- 上架状态：{product.product_status}\n"
                f"- 交易方式：{', '.join(deal_methods)}\n"
                f"- 相关评价数：{len(reviews)}条\n"
                f"请给出购买建议、风险评估和购前检查清单。"
            )
            result_data = self.ai_provider.structured_chat(
                [LLMMessage(role="user", content=user_content)],
                schema=schema,
                max_tokens=2000,
            )
            summary = result_data.get("summary", "")
            risk_level = result_data.get("risk_level", "MEDIUM")
            risk_flags = result_data.get("risk_flags") or []
            next_questions = result_data.get("next_questions") or []
            checklist = result_data.get("checklist") or []
            if not summary and not risk_flags and not next_questions and not checklist:
                raise ValueError("LLM returned empty structured result")
            result = {
                "product_id": product_id,
                "summary": summary,
                "pricing_view": result_data.get("pricing_view", ""),
                "risk_level": risk_level,
                "risk_flags": risk_flags,
                "next_questions": next_questions,
                "checklist": checklist,
                **self._ai_meta(0.84),
            }
        except Exception as exc:
            logger.warning(f"ai_purchase_insights LLM call failed, falling back: {exc}")
            price_band = "价格处于正常观察区间"
            if product.price <= 200:
                price_band = "价格偏低，建议重点核实实物与配件完整度"
            elif product.price >= 3000:
                price_band = "单价较高，建议优先面交或视频验货"
            result = {
                "product_id": product_id,
                "summary": f"这件商品当前状态为{product.audit_status} / {product.product_status}，更适合先确认成色、配件和交付方式后再决定。",
                "pricing_view": price_band,
                "risk_level": "LOW" if product.audit_status == "APPROVED" else "MEDIUM",
                "risk_flags": [
                    "平台审核通过不代表免验货，二手交易仍建议补确认细节。",
                    f"建议优先确认 {' / '.join(deal_methods)} 的具体安排。",
                ],
                "next_questions": [
                    "有没有新的瑕疵细节图？",
                    "是否支持现场验货或视频验货？",
                    "默认交付方式和时效是什么？",
                ],
                "checklist": [
                    "核对配件是否齐全",
                    "核对成色和磨损位置",
                    "确认交易方式和售后边界",
                    f"参考公开商品评价 {len(reviews)} 条",
                ],
                **self._ai_meta(0.69),
            }
        self.repo.log_ai_task("purchase_insights", f"product:{product_id}", result)
        self.db.commit()
        return result

    def ai_chat_copilot(self, session_id: int) -> dict:
        messages = (
            self.db.query(ChatMessage)
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        joined = " ".join(message.content for message in messages[:8]).strip()
        try:
            schema = {
                "summary": "string (对话摘要, 60-120字)",
                "pending_topics": ["array of strings (还未确认的重要议题, 1-4条)"],
                "next_actions": ["array of strings (下一步建议行动, 1-3条)"],
                "suggested_replies": ["array of strings (建议用户发送的回复, 2-3条)"],
            }
            user_content = (
                f"分析以下二手商品买卖双方的对话记录，识别未确认的关键信息，并给出下一步沟通建议。\n"
                f"对话内容：{joined or '（无有效对话内容）'}\n"
                f"请给出对话摘要、待确认议题、行动建议和推荐回复。"
            )
            result_data = self.ai_provider.structured_chat(
                [LLMMessage(role="user", content=user_content)],
                schema=schema,
                max_tokens=2000,
            )
            result = {
                "session_id": session_id,
                "summary": result_data.get("summary", joined[:180] if joined else ""),
                "pending_topics": result_data.get("pending_topics", []),
                "next_actions": result_data.get("next_actions", []),
                "suggested_replies": result_data.get("suggested_replies", []),
                **self._ai_meta(0.84 if messages else 0.4),
            }
        except Exception as exc:
            logger.warning(f"ai_chat_copilot LLM call failed, falling back: {exc}")
            pending_topics: list[str] = []
            if "验货" not in joined:
                pending_topics.append("验货方式")
            if "邮寄" not in joined and "面交" not in joined and "自提" not in joined:
                pending_topics.append("交付方式")
            if "配件" not in joined:
                pending_topics.append("配件完整度")
            if "价格" not in joined and "小刀" not in joined:
                pending_topics.append("价格空间")
            result = {
                "session_id": session_id,
                "summary": joined[:180] if joined else "当前会话还没有有效聊天内容，建议先说明你最关心的成色、配件和交付方式。",
                "pending_topics": pending_topics,
                "next_actions": [
                    "把待确认问题一次性问清，减少来回沟通成本。",
                    "确认交付方式后再决定是否下单。",
                ],
                "suggested_replies": [
                    "能补几张细节图吗？我想先确认成色和瑕疵位置。",
                    "默认是面交、邮寄还是自提？支持先验货再下单吗？",
                    "配件是否齐全，是否有原包装或购买凭证？",
                ],
                **self._ai_meta(0.64 if messages else 0.4),
            }
        self.repo.log_ai_task("chat_copilot", f"session:{session_id}", result)
        self.db.commit()
        return result

    def ai_control_panel(self) -> dict:
        status = self.ai_provider.status()
        task_total = self.db.query(AITaskLog).count()
        failed_tasks = self.db.query(AITaskLog).filter(AITaskLog.status == "FAILED").count()
        latest_tasks = self.repo.list_ai_tasks(limit=10)
        return {
            "provider": {
                "name": status.provider,
                "source_mode": status.source_mode,
                "degraded": status.degraded,
                "configured": bool(get_settings().ai_api_key),
            },
            "quality": {
                "task_total": task_total,
                "failed_tasks": failed_tasks,
                "success_rate": round(((task_total - failed_tasks) / task_total) * 100, 1) if task_total else 100.0,
                "fallback_rate": 100.0 if status.degraded else 0.0,
            },
            "recent_tasks": [
                {
                    "id": item.id,
                    "task_name": item.task_name,
                    "status": item.status,
                    "prompt": item.prompt,
                    "result": item.result,
                    "created_at": item.created_at,
                }
                for item in latest_tasks
            ],
        }

    def overview(self):
        products = len(self.catalog_repo.list_products())
        pending = len(self.catalog_repo.list_pending_products())
        jobs = self.db.query(JobRunLog).count()
        reports = self.db.query(Report).count()
        orders = self.db.query(Order).count()
        return {"products": products, "pending_audits": pending, "job_count": jobs, "reports": reports, "orders": orders}

    def charts(self):
        order_status = [
            {"name": status or "UNKNOWN", "value": count}
            for status, count in self.db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
        ]
        report_outcome = [
            {"name": status or "UNKNOWN", "value": count}
            for status, count in self.db.query(Report.status, func.count(Report.id)).group_by(Report.status).all()
        ]
        return {
            "orderStatus": order_status,
            "auditQueue": [{"name": "PENDING", "value": len(self.catalog_repo.list_pending_products())}],
            "reportOutcome": report_outcome,
        }

    def recommendation_workbench(self):
        materials = self.repo.list_materials(limit=30)
        snapshots = self.repo.list_snapshots(limit=12)
        jobs = self.repo.list_jobs(limit=12)
        ai_tasks = self.repo.list_ai_tasks(limit=12)

        material_type_counts = [
            {"name": material_type, "value": count}
            for material_type, count in (
                self.db.query(RecommendationMaterial.material_type, func.count(RecommendationMaterial.id))
                .group_by(RecommendationMaterial.material_type)
                .order_by(func.count(RecommendationMaterial.id).desc())
                .all()
            )
        ]
        snapshot_scene_counts = [
            {"name": scene, "value": count}
            for scene, count in (
                self.db.query(RecommendationSnapshot.scene, func.count(RecommendationSnapshot.id))
                .group_by(RecommendationSnapshot.scene)
                .order_by(func.count(RecommendationSnapshot.id).desc())
                .all()
            )
        ]

        user_ids = {item.user_id for item in materials if item.user_id is not None}
        user_ids.update(item.user_id for item in snapshots if item.user_id is not None)
        user_map = (
            {user.id: user.display_name for user in self.db.query(User).filter(User.id.in_(user_ids)).all()}
            if user_ids
            else {}
        )

        product_ids = {item.product_id for item in materials if item.product_id is not None}
        product_ids.update(
            candidate.get("product_id")
            for snapshot in snapshots
            for candidate in snapshot.payload.get("items", [])
            if candidate.get("product_id") is not None
        )
        product_map = (
            {product.id: product for product in self.db.query(Product).filter(Product.id.in_(product_ids)).all()}
            if product_ids
            else {}
        )

        def format_material(item: RecommendationMaterial) -> dict:
            product = product_map.get(item.product_id)
            return {
                "id": item.id,
                "user_id": item.user_id,
                "user_name": user_map.get(item.user_id, "Anonymous") if item.user_id else "Anonymous",
                "product_id": item.product_id,
                "product_title": product.title if product else "Unknown product",
                "material_type": item.material_type,
                "payload": item.payload,
                "created_at": item.created_at,
            }

        def format_snapshot(item: RecommendationSnapshot) -> dict:
            raw_items = item.payload.get("items", [])
            hydrated_items = []
            for candidate in raw_items[:3]:
                product = product_map.get(candidate.get("product_id"))
                hydrated_items.append(
                    {
                        "product_id": candidate.get("product_id"),
                        "title": candidate.get("title") or (product.title if product else "Unknown product"),
                        "reason": candidate.get("reason", "Behavior-based recommendation"),
                    }
                )
            return {
                "id": item.id,
                "user_id": item.user_id,
                "user_name": user_map.get(item.user_id, "Anonymous") if item.user_id else "Anonymous",
                "scene": item.scene,
                "item_count": len(raw_items),
                "items": hydrated_items,
                "updated_at": item.updated_at,
            }

        return {
            "summary": {
                "materials": self.db.query(RecommendationMaterial).count(),
                "snapshots": self.db.query(RecommendationSnapshot).count(),
                "jobs": self.db.query(JobRunLog).count(),
                "ai_tasks": self.db.query(AITaskLog).count(),
            },
            "charts": {
                "materialTypes": material_type_counts,
                "snapshotScenes": snapshot_scene_counts,
            },
            "materials": [format_material(item) for item in materials],
            "snapshots": [format_snapshot(item) for item in snapshots],
            "jobs": [
                {
                    "id": item.id,
                    "job_name": item.job_name,
                    "status": item.status,
                    "details": item.details,
                    "created_at": item.created_at,
                }
                for item in jobs
            ],
            "aiTasks": [
                {
                    "id": item.id,
                    "task_name": item.task_name,
                    "status": item.status,
                    "prompt": item.prompt,
                    "result": item.result,
                    "created_at": item.created_at,
                }
                for item in ai_tasks
            ],
        }

    def platform_ops(self):
        recent_jobs = self.repo.list_jobs(limit=12)
        failed_jobs = self.db.query(JobRunLog).filter(JobRunLog.status == "FAILED").order_by(JobRunLog.created_at.desc()).limit(8).all()
        event_counts = [
            {"name": event_type, "value": count}
            for event_type, count in (
                self.db.query(DomainEventRecord.event_type, func.count(DomainEventRecord.id))
                .group_by(DomainEventRecord.event_type)
                .order_by(func.count(DomainEventRecord.id).desc())
                .all()
            )
        ]
        job_status_counts = [
            {"name": status or "UNKNOWN", "value": count}
            for status, count in (
                self.db.query(JobRunLog.status, func.count(JobRunLog.id))
                .group_by(JobRunLog.status)
                .order_by(func.count(JobRunLog.id).desc())
                .all()
            )
        ]
        pending_audits = self.db.query(AuditTask).filter(AuditTask.status == "PENDING").count()
        search_health = self.search.health()
        settings = get_settings()
        redis_check = self._check_redis(settings)
        readiness = [
            self._check_database(),
            redis_check,
            self._check_async_tasks(redis_check["status"] == "READY"),
            self._check_storage(settings),
            self._check_search(search_health),
        ]

        return {
            "summary": {
                "events": self.db.query(DomainEventRecord).count(),
                "pending_jobs": self.db.query(JobRunLog).filter(JobRunLog.status == "PENDING").count(),
                "failed_jobs": self.db.query(JobRunLog).filter(JobRunLog.status == "FAILED").count(),
                "pending_audits": pending_audits,
                "storage_backend": settings.storage_backend,
            },
            "runtime": {
                "app_env": settings.app_env,
                "storage_backend": settings.storage_backend,
                "ai_provider": settings.ai_provider,
            },
            "search": search_health,
            "readiness": readiness,
            "runbook": self._runbook(),
            "charts": {
                "eventTypes": event_counts,
                "jobStatuses": job_status_counts,
            },
            "jobs": [
                {
                    "id": item.id,
                    "job_name": item.job_name,
                    "status": item.status,
                    "details": item.details,
                    "created_at": item.created_at,
                }
                for item in recent_jobs
            ],
            "failedJobs": [
                {
                    "id": item.id,
                    "job_name": item.job_name,
                    "status": item.status,
                    "details": item.details,
                    "created_at": item.created_at,
                }
                for item in failed_jobs
            ],
            "events": event_counts[:12],
        }
