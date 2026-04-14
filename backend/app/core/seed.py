from app.core.enums import AppealStatus, AuditStatus, MessageStatus, OrderStatus, ProductStatus, ReportStatus, TaskStatus
from app.core.security import hash_password
from app.models.entities import (
    AITaskLog,
    Appeal,
    AuditTask,
    BrowseHistory,
    Category,
    ChatMessage,
    ChatSession,
    Favorite,
    JobRunLog,
    Notification,
    Order,
    OrderItem,
    Permission,
    Product,
    RecommendationMaterial,
    RecommendationSnapshot,
    Report,
    Review,
    Role,
    RolePermission,
    User,
    UserRole,
)


def seed_defaults(db) -> None:
    if db.query(User).first():
        return

    permission_specs = [
        ("product.audit", "Audit products"),
        ("report.review", "Review reports"),
        ("appeal.review", "Review appeals"),
        ("recommendation.manage", "Manage recommendations"),
        ("search.manage", "Manage search"),
    ]
    permissions = [Permission(code=code, name=name) for code, name in permission_specs]
    admin_role = Role(name="Administrator", code="ADMIN")
    moderator_role = Role(name="Moderator", code="MODERATOR")

    admin = User(
        email="admin@example.com",
        password_hash=hash_password("Admin123!"),
        display_name="System Admin",
        is_admin=True,
    )
    seller = User(
        email="seller@example.com",
        password_hash=hash_password("Seller123!"),
        display_name="Demo Seller",
        is_admin=False,
    )
    buyer = User(
        email="buyer@example.com",
        password_hash=hash_password("Buyer123!"),
        display_name="Demo Buyer",
        is_admin=False,
    )
    reviewer = User(
        email="moderator@example.com",
        password_hash=hash_password("Mod123456!"),
        display_name="Audit Operator",
        is_admin=True,
    )

    categories = [
        Category(name="数码"),
        Category(name="图书"),
        Category(name="家居"),
        Category(name="潮玩"),
    ]

    db.add_all([admin_role, moderator_role, admin, seller, buyer, reviewer, *permissions, *categories])
    db.flush()

    code_to_permission = {permission.code: permission for permission in permissions}
    db.add_all(
        [
            UserRole(user_id=admin.id, role_id=admin_role.id),
            UserRole(user_id=reviewer.id, role_id=moderator_role.id),
            *[
                RolePermission(role_id=admin_role.id, permission_id=permission.id)
                for permission in permissions
            ],
            RolePermission(role_id=moderator_role.id, permission_id=code_to_permission["product.audit"].id),
            RolePermission(role_id=moderator_role.id, permission_id=code_to_permission["report.review"].id),
            RolePermission(role_id=moderator_role.id, permission_id=code_to_permission["appeal.review"].id),
        ]
    )

    category_map = {category.name: category.id for category in categories}
    approved_product = Product(
        seller_id=seller.id,
        category_id=category_map["数码"],
        title="Nintendo Switch OLED 九成新",
        description="含原装底座、手柄和收纳包，支持现场验机。",
        price=1799.0,
        stock=1,
        product_status=ProductStatus.ACTIVE.value,
        audit_status=AuditStatus.APPROVED.value,
        tags={"keywords": ["switch", "oled", "九成新"]},
    )
    second_product = Product(
        seller_id=seller.id,
        category_id=category_map["图书"],
        title="算法竞赛进阶指南",
        description="书页完整，有少量笔记，适合刷题入门。",
        price=68.0,
        stock=2,
        product_status=ProductStatus.ACTIVE.value,
        audit_status=AuditStatus.APPROVED.value,
        tags={"keywords": ["算法", "图书"]},
    )
    pending_product = Product(
        seller_id=seller.id,
        category_id=category_map["潮玩"],
        title="限定款手办展示件",
        description="盒损轻微，主体完好，等待管理员审核。",
        price=399.0,
        stock=1,
        product_status=ProductStatus.DRAFT.value,
        audit_status=AuditStatus.PENDING.value,
        tags={"keywords": ["手办", "限定"]},
    )
    db.add_all([approved_product, second_product, pending_product])
    db.flush()

    audit_task = AuditTask(
        task_type="PRODUCT_AUDIT",
        entity_type="PRODUCT",
        entity_id=pending_product.id,
        status=TaskStatus.PENDING.value,
        payload={"title": pending_product.title},
    )
    report = Report(
        reporter_id=buyer.id,
        target_type="PRODUCT",
        target_id=approved_product.id,
        reason="商品描述与成色信息可能不一致",
        status=ReportStatus.PROCESSED.value,
        decision="已提醒卖家补充说明并记录一次治理事件",
    )
    db.add_all([audit_task, report])
    db.flush()

    appeal = Appeal(
        report_id=report.id,
        applicant_id=seller.id,
        reason="已补充更多细节图，申请复核",
        status=AppealStatus.PENDING.value,
    )
    db.add(appeal)
    db.flush()

    appeal_task = AuditTask(
        task_type="APPEAL_REVIEW",
        entity_type="APPEAL",
        entity_id=appeal.id,
        status=TaskStatus.PENDING.value,
        payload={"reason": appeal.reason},
    )
    order = Order(
        buyer_id=buyer.id,
        seller_id=seller.id,
        product_id=approved_product.id,
        total_amount=1799.0,
        status=OrderStatus.COMPLETED.value,
    )
    db.add_all([appeal_task, order])
    db.flush()

    db.add(OrderItem(order_id=order.id, product_id=approved_product.id, quantity=1, unit_price=1799.0))
    db.add(
        Review(
            order_id=order.id,
            product_id=approved_product.id,
            user_id=buyer.id,
            rating=5,
            content="成色很好，沟通顺畅，和描述基本一致。",
        )
    )
    db.add(Favorite(user_id=buyer.id, product_id=approved_product.id))
    db.add(BrowseHistory(user_id=buyer.id, product_id=approved_product.id))
    db.add(
        RecommendationMaterial(
            user_id=buyer.id,
            product_id=approved_product.id,
            material_type="ORDER",
            payload={"order_id": order.id},
        )
    )
    db.add(
        RecommendationSnapshot(
            user_id=buyer.id,
            scene="HOME",
            payload={"items": [{"product_id": approved_product.id, "title": approved_product.title}]},
        )
    )

    session = ChatSession(product_id=approved_product.id, buyer_id=buyer.id, seller_id=seller.id)
    db.add(session)
    db.flush()
    db.add_all(
        [
            ChatMessage(session_id=session.id, sender_id=buyer.id, content="这台机器还在吗？", status=MessageStatus.READ.value),
            ChatMessage(session_id=session.id, sender_id=seller.id, content="还在，可以现场验机。", status=MessageStatus.SENT.value),
        ]
    )
    db.add(
        Notification(
            user_id=buyer.id,
            event_type="AUDIT",
            title="举报处理完成",
            content="你提交的举报已经进入处理完成状态。",
        )
    )
    db.add(
        JobRunLog(
            job_name="recommendation_rebuild",
            status=TaskStatus.COMPLETED.value,
            details={"scene": "HOME"},
        )
    )
    db.add(
        AITaskLog(
            task_name="product_draft",
            prompt="switch, 九成新, 原装配件",
            result={"title": "Nintendo Switch OLED 九成新", "risk_level": "LOW"},
            status=TaskStatus.COMPLETED.value,
        )
    )
    db.commit()
