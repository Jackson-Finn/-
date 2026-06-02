from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.errors import register_error_handlers
from app.core.realtime import manager
from app.core.seed import seed_defaults
from app.core.storage import get_storage_service


@asynccontextmanager
async def lifespan(_: FastAPI):
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
