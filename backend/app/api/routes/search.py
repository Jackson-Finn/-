from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.services.catalog import CatalogService


router = APIRouter()


@router.get("/products")
def search_products(keyword: str | None = Query(default=None), db: Session = Depends(get_db)):
    products = CatalogService(db).list_products(keyword)
    return APIResponse(data=[{"id": product.id, "title": product.title, "price": product.price} for product in products])


@router.get("/suggest")
def suggest(keyword: str | None = Query(default=None), db: Session = Depends(get_db)):
    suggestions = CatalogService(db).suggest(keyword)
    return APIResponse(data={"suggestions": suggestions})
