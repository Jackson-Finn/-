from pydantic import BaseModel
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.services.catalog import CatalogService


router = APIRouter()


class UploadInitRequest(BaseModel):
    filename: str
    mime_type: str


class UploadCompleteRequest(BaseModel):
    asset_id: int
    width: int | None = None
    height: int | None = None


@router.post("/upload-init")
def upload_init(payload: UploadInitRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    asset = CatalogService(db).upload_init(current_user.id, payload.filename, payload.mime_type)
    return APIResponse(
        data={
            "id": asset.id,
            "object_key": asset.object_key,
            "url": asset.url,
            "upload_path": f"/api/media/{asset.id}/file",
        }
    )


@router.post("/{asset_id}/file")
def upload_file(
    asset_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = CatalogService(db).upload_file(asset_id, current_user.id, file)
    return APIResponse(data={"id": asset.id, "url": asset.url, "metadata": asset.metadata_json})


@router.post("/complete")
def upload_complete(payload: UploadCompleteRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    asset = CatalogService(db).complete_upload(payload.asset_id, current_user.id, payload.width, payload.height)
    return APIResponse(data={"id": asset.id, "url": asset.url, "metadata": asset.metadata_json})
