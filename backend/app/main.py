from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.errors import register_error_handlers
from app.core.realtime import manager
from app.core.seed import seed_defaults
from app.core.storage import get_storage_service


def ensure_runtime_columns() -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        user_columns = {column["name"] for column in inspector.get_columns("users")} if inspector.has_table("users") else set()
        if "presence_status" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN presence_status VARCHAR(32) DEFAULT 'ONLINE'"))
            connection.execute(text("UPDATE users SET presence_status = COALESCE(presence_status, 'ONLINE')"))

        review_columns = {column["name"] for column in inspector.get_columns("reviews")} if inspector.has_table("reviews") else set()
        if "review_type" not in review_columns:
            connection.execute(text("ALTER TABLE reviews ADD COLUMN review_type VARCHAR(32) DEFAULT 'PRODUCT'"))
            connection.execute(text("UPDATE reviews SET review_type = COALESCE(review_type, 'PRODUCT')"))
        if "seller_id" not in review_columns:
            connection.execute(text("ALTER TABLE reviews ADD COLUMN seller_id INTEGER"))
            connection.execute(
                text(
                    """
                    UPDATE reviews
                    SET seller_id = (
                      SELECT orders.seller_id
                      FROM orders
                      WHERE orders.id = reviews.order_id
                    )
                    WHERE seller_id IS NULL
                    """
                )
            )

        notification_columns = {column["name"] for column in inspector.get_columns("notifications")} if inspector.has_table("notifications") else set()
        if "action_target" not in notification_columns:
            connection.execute(text("ALTER TABLE notifications ADD COLUMN action_target VARCHAR(255)"))

        broadcast_columns = {column["name"] for column in inspector.get_columns("admin_notification_broadcasts")} if inspector.has_table("admin_notification_broadcasts") else set()
        if "action_target" not in broadcast_columns:
            connection.execute(text("ALTER TABLE admin_notification_broadcasts ADD COLUMN action_target VARCHAR(255)"))

        if inspector.has_table("browse_history"):
            connection.execute(
                text(
                    """
                    DELETE FROM browse_history
                    WHERE id IN (
                      SELECT duplicate_ids.id
                      FROM (
                        SELECT older.id
                        FROM browse_history AS older
                        JOIN browse_history AS newer
                          ON older.user_id = newer.user_id
                         AND older.product_id = newer.product_id
                         AND (
                           older.updated_at < newer.updated_at
                           OR (older.updated_at = newer.updated_at AND older.id < newer.id)
                         )
                      ) AS duplicate_ids
                    )
                    """
                )
            )


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_runtime_columns()
    try:
        get_storage_service().bootstrap()
    except Exception as exc:
        print(f"[storage] bootstrap skipped: {exc}")
    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()
    yield


settings = get_settings()
if settings.storage_backend == "local":
    Path(settings.media_storage_dir).mkdir(parents=True, exist_ok=True)
app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)
app.include_router(api_router, prefix=settings.api_prefix)
if settings.storage_backend == "local":
    app.mount("/uploads", StaticFiles(directory=settings.media_storage_dir), name="uploads")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    user_id = int(websocket.query_params.get("user_id", "0") or 0)
    if not user_id:
        await websocket.close(code=1008)
        return
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
