from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.user import SellerProductSummary, SellerProfileResponse
from app.services.identity import IdentityService


router = APIRouter()


@router.get("/{user_id:int}")
def get_public_seller(user_id: int, db: Session = Depends(get_db)):
    service = IdentityService(db)
    seller = service.get_public_seller(user_id)
    return APIResponse(data=SellerProfileResponse.model_validate(seller))


@router.get("/{user_id:int}/products")
def list_public_seller_products(user_id: int, db: Session = Depends(get_db)):
    service = IdentityService(db)
    products = service.list_public_seller_products(user_id)
    return APIResponse(data=[SellerProductSummary.model_validate(product) for product in products])
