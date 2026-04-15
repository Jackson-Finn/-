from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_permissions
from app.schemas.common import APIResponse
from app.schemas.governance import ReviewDecisionRequest, TaskDecisionRequest
from app.schemas.notification import AdminNotificationCreateRequest
from app.schemas.product import AuditDecisionRequest, ProductResponse
from app.services.catalog import CatalogService
from app.services.governance import GovernanceService
from app.services.identity import IdentityService
from app.services.intelligence import IntelligenceService
from app.services.interaction import InteractionService


router = APIRouter()


class AssignRolesRequest(BaseModel):
    role_ids: list[int]


class AdminProductOffShelfRequest(BaseModel):
    note: str | None = None


@router.get("/users")
def list_users(_: object = Depends(require_permissions("product.audit")), db: Session = Depends(get_db)):
    users = IdentityService(db).list_users()
    return APIResponse(data=[{"id": user.id, "email": user.email, "display_name": user.display_name, "presence_status": user.presence_status} for user in users])


@router.get("/notification-users")
def list_notification_users(_: object = Depends(require_permissions("notification.manage")), db: Session = Depends(get_db)):
    users = IdentityService(db).list_users()
    return APIResponse(data=[{"id": user.id, "email": user.email, "display_name": user.display_name, "presence_status": user.presence_status} for user in users])


@router.get("/products")
def list_products(
    keyword: str | None = None,
    audit_status: str | None = None,
    product_status: str | None = None,
    sort: str = "newest",
    _: object = Depends(require_permissions("product.audit")),
    db: Session = Depends(get_db),
):
    service = CatalogService(db)
    products = service.repo.list_admin_products(
        keyword=keyword,
        audit_status=audit_status,
        product_status=product_status,
        sort=sort,
    )
    return APIResponse(data=[ProductResponse.model_validate(service.serialize_product(product)) for product in products])


@router.get("/products/pending")
def list_pending(_: object = Depends(require_permissions("product.audit")), db: Session = Depends(get_db)):
    service = CatalogService(db)
    products = service.list_pending()
    return APIResponse(data=[ProductResponse.model_validate(service.serialize_product(product)) for product in products])


@router.get("/products/{product_id}")
def product_context(
    product_id: int,
    current_user: object = Depends(require_permissions("product.audit")),
    db: Session = Depends(get_db),
):
    context = CatalogService(db).admin_product_context(product_id, actor_id=current_user.id)
    return APIResponse(
        data={
            "product": context["product"],
            "tasks": [
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "entity_type": task.entity_type,
                    "entity_id": task.entity_id,
                    "status": task.status,
                    "payload": task.payload,
                    "created_at": task.created_at,
                }
                for task in context["tasks"]
            ],
            "reports": [
                {
                    "id": report.id,
                    "status": report.status,
                    "reason": report.reason,
                    "decision": report.decision,
                    "created_at": report.created_at,
                }
                for report in context["reports"]
            ],
            "operations": [
                {
                    "id": item.id,
                    "actor_id": item.actor_id,
                    "action": item.action,
                    "details": item.details,
                    "created_at": item.created_at,
                }
                for item in context["operations"]
            ],
        }
    )


@router.post("/products/{product_id}/audit")
def audit_product(
    product_id: int,
    payload: AuditDecisionRequest,
    current_user: object = Depends(require_permissions("product.audit")),
    db: Session = Depends(get_db),
):
    service = CatalogService(db)
    product = service.audit_product(product_id, payload, actor_id=current_user.id)
    return APIResponse(data=ProductResponse.model_validate(service.serialize_product(product)))


@router.post("/products/{product_id}/off-shelf")
def admin_off_shelf(
    product_id: int,
    payload: AdminProductOffShelfRequest,
    current_user: object = Depends(require_permissions("product.audit")),
    db: Session = Depends(get_db),
):
    service = CatalogService(db)
    product = service.admin_off_shelf(product_id, actor_id=current_user.id, note=payload.note)
    return APIResponse(data=ProductResponse.model_validate(service.serialize_product(product)))


@router.get("/reports")
def list_reports(_: object = Depends(require_permissions("report.review")), db: Session = Depends(get_db)):
    reports = GovernanceService(db).list_reports()
    return APIResponse(
        data=[
            {
                "id": report.id,
                "reporter_id": report.reporter_id,
                "target_type": report.target_type,
                "target_id": report.target_id,
                "status": report.status,
                "reason": report.reason,
                "decision": report.decision,
                "created_at": report.created_at,
            }
            for report in reports
        ]
    )


@router.post("/reports/{report_id}/process")
async def process_report(
    report_id: int,
    payload: ReviewDecisionRequest,
    current_user: object = Depends(require_permissions("report.review")),
    db: Session = Depends(get_db),
):
    report = await GovernanceService(db).process_report(
        report_id,
        payload.note,
        payload.approved,
        actor_id=current_user.id,
    )
    return APIResponse(data={"id": report.id, "status": report.status, "decision": report.decision})


@router.get("/reports/{report_id}/context")
def report_context(report_id: int, _: object = Depends(require_permissions("report.review")), db: Session = Depends(get_db)):
    context = GovernanceService(db).report_context(report_id)
    report = context["report"]
    return APIResponse(
        data={
            "report": {
                "id": report.id,
                "reporter_id": report.reporter_id,
                "target_type": report.target_type,
                "target_id": report.target_id,
                "status": report.status,
                "reason": report.reason,
                "decision": report.decision,
                "created_at": report.created_at,
            },
            "tasks": [
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "entity_type": task.entity_type,
                    "entity_id": task.entity_id,
                    "status": task.status,
                    "payload": task.payload,
                    "created_at": task.created_at,
                }
                for task in context["tasks"]
            ],
            "operations": [
                {
                    "id": item.id,
                    "actor_id": item.actor_id,
                    "action": item.action,
                    "details": item.details,
                    "created_at": item.created_at,
                }
                for item in context["operations"]
            ],
        }
    )


@router.get("/appeals")
def list_appeals(_: object = Depends(require_permissions("appeal.review")), db: Session = Depends(get_db)):
    appeals = GovernanceService(db).list_appeals()
    return APIResponse(
        data=[
            {
                "id": appeal.id,
                "report_id": appeal.report_id,
                "applicant_id": appeal.applicant_id,
                "status": appeal.status,
                "reason": appeal.reason,
                "decision": appeal.decision,
                "created_at": appeal.created_at,
            }
            for appeal in appeals
        ]
    )


@router.post("/appeals/{appeal_id}/review")
async def review_appeal(
    appeal_id: int,
    payload: ReviewDecisionRequest,
    current_user: object = Depends(require_permissions("appeal.review")),
    db: Session = Depends(get_db),
):
    appeal = await GovernanceService(db).review_appeal(appeal_id, payload, actor_id=current_user.id)
    return APIResponse(data={"id": appeal.id, "status": appeal.status, "decision": appeal.decision})


@router.get("/appeals/{appeal_id}/context")
def appeal_context(appeal_id: int, _: object = Depends(require_permissions("appeal.review")), db: Session = Depends(get_db)):
    context = GovernanceService(db).appeal_context(appeal_id)
    appeal = context["appeal"]
    report = context["report"]
    return APIResponse(
        data={
            "appeal": {
                "id": appeal.id,
                "report_id": appeal.report_id,
                "applicant_id": appeal.applicant_id,
                "status": appeal.status,
                "reason": appeal.reason,
                "decision": appeal.decision,
                "created_at": appeal.created_at,
            },
            "report": {
                "id": report.id,
                "status": report.status,
                "reason": report.reason,
                "decision": report.decision,
                "target_type": report.target_type,
                "target_id": report.target_id,
                "created_at": report.created_at,
            }
            if report
            else None,
            "tasks": [
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "entity_type": task.entity_type,
                    "entity_id": task.entity_id,
                    "status": task.status,
                    "payload": task.payload,
                    "created_at": task.created_at,
                }
                for task in context["tasks"]
            ],
            "operations": [
                {
                    "id": item.id,
                    "actor_id": item.actor_id,
                    "action": item.action,
                    "details": item.details,
                    "created_at": item.created_at,
                }
                for item in context["operations"]
            ],
        }
    )


@router.get("/audit/tasks")
def list_audit_tasks(_: object = Depends(require_permissions("product.audit")), db: Session = Depends(get_db)):
    tasks = GovernanceService(db).list_audit_tasks()
    return APIResponse(
        data=[
            {
                "id": task.id,
                "task_type": task.task_type,
                "entity_type": task.entity_type,
                "entity_id": task.entity_id,
                "status": task.status,
                "payload": task.payload,
                "created_at": task.created_at,
            }
            for task in tasks
        ]
    )


@router.get("/operations")
def list_operations(_: object = Depends(require_permissions("product.audit")), db: Session = Depends(get_db)):
    operations = GovernanceService(db).list_operation_logs()
    return APIResponse(
        data=[
            {
                "id": item.id,
                "actor_id": item.actor_id,
                "action": item.action,
                "details": item.details,
                "created_at": item.created_at,
            }
            for item in operations
        ]
    )


@router.post("/audit/tasks/{task_id}/decision")
async def decide_task(
    task_id: int,
    payload: TaskDecisionRequest,
    current_user: object = Depends(require_permissions("product.audit")),
    db: Session = Depends(get_db),
):
    task = await GovernanceService(db).decide_task(task_id, payload, actor_id=current_user.id)
    return APIResponse(data={"id": task.id, "status": task.status, "payload": task.payload})


@router.get("/statistics/overview")
def overview(_: object = Depends(require_permissions("product.audit")), db: Session = Depends(get_db)):
    return APIResponse(data=IntelligenceService(db).overview())


@router.get("/statistics/charts")
def charts(_: object = Depends(require_permissions("product.audit")), db: Session = Depends(get_db)):
    return APIResponse(data=IntelligenceService(db).charts())


@router.post("/recommendations/rebuild")
def rebuild(_: object = Depends(require_permissions("recommendation.manage")), db: Session = Depends(get_db)):
    return APIResponse(data=IntelligenceService(db).rebuild_recommendations())


@router.get("/recommendations/workbench")
def recommendation_workbench(
    _: object = Depends(require_permissions("recommendation.manage")),
    db: Session = Depends(get_db),
):
    return APIResponse(data=IntelligenceService(db).recommendation_workbench())


@router.post("/search/reindex")
def reindex(_: object = Depends(require_permissions("search.manage")), db: Session = Depends(get_db)):
    return APIResponse(data=IntelligenceService(db).reindex_search())


@router.get("/platform/ops")
def platform_ops(_: object = Depends(require_permissions("product.audit")), db: Session = Depends(get_db)):
    return APIResponse(data=IntelligenceService(db).platform_ops())


@router.get("/ai/control")
def ai_control(_: object = Depends(require_permissions("recommendation.manage")), db: Session = Depends(get_db)):
    return APIResponse(data=IntelligenceService(db).ai_control_panel())


@router.post("/notifications")
async def publish_notification(
    payload: AdminNotificationCreateRequest,
    current_user: object = Depends(require_permissions("notification.manage")),
    db: Session = Depends(get_db),
):
    return APIResponse(data=await InteractionService(db).publish_admin_notification(current_user.id, payload))


@router.get("/notifications")
def list_admin_notifications(
    _: object = Depends(require_permissions("notification.manage")),
    db: Session = Depends(get_db),
):
    return APIResponse(data=InteractionService(db).list_admin_broadcasts())


@router.get("/roles")
def list_roles(_: object = Depends(require_permissions("product.audit")), db: Session = Depends(get_db)):
    roles = IdentityService(db).list_roles()
    return APIResponse(data=[{"id": role.id, "name": role.name, "code": role.code} for role in roles])


@router.get("/permissions")
def list_permissions(_: object = Depends(require_permissions("product.audit")), db: Session = Depends(get_db)):
    permissions = IdentityService(db).list_permissions()
    return APIResponse(data=[{"id": permission.id, "code": permission.code, "name": permission.name} for permission in permissions])


@router.post("/users/{user_id}/roles")
def assign_roles(
    user_id: int,
    payload: AssignRolesRequest,
    _: object = Depends(require_permissions("product.audit")),
    db: Session = Depends(get_db),
):
    IdentityService(db).assign_roles(user_id, payload.role_ids)
    return APIResponse(message="Roles assigned")
