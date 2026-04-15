from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permissions
from app.schemas.common import APIResponse
from app.schemas.product import AuditDecisionRequest, ProductCreateRequest, ProductResponse, ProductUpdateRequest
from app.services.catalog import CatalogService


router = APIRouter()


@router.get("")
def list_products(keyword: str | None = Query(default=None), db: Session = Depends(get_db)):
    products = CatalogService(db).list_products(keyword)
    service = CatalogService(db)
    return APIResponse(data=[ProductResponse.model_validate(service.serialize_product(product)) for product in products])


@router.get("/mine")
def list_my_products(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    service = CatalogService(db)
    products = service.list_my_products(current_user.id)
    return APIResponse(data=[ProductResponse.model_validate(service.serialize_product(product)) for product in products])


@router.get("/{product_id:int}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    service = CatalogService(db)
    product = service.get_product(product_id)
    return APIResponse(data=ProductResponse.model_validate(service.serialize_product(product)))


@router.post("")
def create_product(payload: ProductCreateRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    service = CatalogService(db)
    product = service.create_product(current_user.id, payload)
    return APIResponse(data=ProductResponse.model_validate(service.serialize_product(product)))


@router.put("/{product_id:int}")
def update_product(
    product_id: int,
    payload: ProductUpdateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = CatalogService(db)
    product = service.update_product(product_id, current_user.id, payload)
    return APIResponse(data=ProductResponse.model_validate(service.serialize_product(product)))


@router.post("/{product_id:int}/off-shelf")
def off_shelf(product_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    service = CatalogService(db)
    product = service.off_shelf(product_id, current_user.id)
    return APIResponse(data=ProductResponse.model_validate(service.serialize_product(product)))


@router.post("/{product_id:int}/resubmit")
def resubmit_product(product_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    service = CatalogService(db)
    product = service.resubmit_product(product_id, current_user.id)
    return APIResponse(data=ProductResponse.model_validate(service.serialize_product(product)))


@router.get("/admin/pending")
def list_pending(_: object = Depends(require_permissions("product.audit")), db: Session = Depends(get_db)):
    service = CatalogService(db)
    products = service.list_pending()
    return APIResponse(data=[ProductResponse.model_validate(service.serialize_product(product)) for product in products])


@router.post("/admin/{product_id:int}/audit")
def audit_product(
    product_id: int,
    payload: AuditDecisionRequest,
    current_user: object = Depends(require_permissions("product.audit")),
    db: Session = Depends(get_db),
):
    service = CatalogService(db)
    product = service.audit_product(product_id, payload, actor_id=current_user.id)
    return APIResponse(data=ProductResponse.model_validate(service.serialize_product(product)))
