from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.services.catalog import CatalogService


router = APIRouter()


@router.get("/products")
def search_products(
    keyword: str | None = Query(default=None),
    category: str | None = Query(default=None),
    condition: str | None = Query(default=None),
    price_min: float | None = Query(default=None),
    price_max: float | None = Query(default=None),
    sort: str = Query(default="newest"),
    delivery_method: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    service = CatalogService(db)
    payload = service.search_products(
        keyword=keyword,
        category=category,
        condition=condition,
        price_min=price_min,
        price_max=price_max,
        sort=sort,
        delivery_method=delivery_method,
    )
    return APIResponse(data=payload)


@router.get("/suggest")
def suggest(keyword: str | None = Query(default=None), db: Session = Depends(get_db)):
    suggestions = CatalogService(db).suggest(keyword)
    return APIResponse(data={"suggestions": suggestions})
