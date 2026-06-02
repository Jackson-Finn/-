"""add coursework database objects

Revision ID: 8d4bf17961d5
Revises: facebdbb9777
Create Date: 2026-06-02 20:40:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8d4bf17961d5"
down_revision: Union[str, Sequence[str], None] = "facebdbb9777"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_products_price_non_negative",
        "products",
        "price >= 0",
    )
    op.create_check_constraint(
        "ck_products_stock_non_negative",
        "products",
        "stock >= 0",
    )
    op.create_check_constraint(
        "ck_reviews_rating_range",
        "reviews",
        "rating BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_order_items_quantity_positive",
        "order_items",
        "quantity > 0",
    )
    op.create_unique_constraint(
        "uq_reviews_order_review_type",
        "reviews",
        ["order_id", "review_type"],
    )

    op.create_index(
        "ix_products_audit_status_product_status_updated_at",
        "products",
        ["audit_status", "product_status", "updated_at"],
        unique=False,
    )
    op.create_index(
        "ix_products_category_status_price",
        "products",
        ["category_id", "product_status", "price"],
        unique=False,
    )
    op.create_index(
        "ix_orders_buyer_status_created_at",
        "orders",
        ["buyer_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_reports_status_created_at",
        "reports",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_tasks_entity_status_created_at",
        "audit_tasks",
        ["entity_type", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_reviews_product_created_at",
        "reviews",
        ["product_id", "created_at"],
        unique=False,
    )

    op.execute("DROP TRIGGER IF EXISTS trg_reports_after_insert_audit_task")
    op.execute("DROP TRIGGER IF EXISTS trg_reports_after_insert_operation_log")
    op.execute("DROP VIEW IF EXISTS vw_active_product_catalog")
    op.execute("DROP VIEW IF EXISTS vw_seller_operational_summary")
    op.execute("DROP VIEW IF EXISTS vw_admin_risk_overview")
    op.execute("DROP FUNCTION IF EXISTS fn_product_display_status")
    op.execute("DROP FUNCTION IF EXISTS fn_seller_trust_level")

    op.execute(
        """
        CREATE FUNCTION fn_product_display_status(
            p_audit_status VARCHAR(32),
            p_product_status VARCHAR(32),
            p_stock INT
        )
        RETURNS VARCHAR(32)
        DETERMINISTIC
        NO SQL
        RETURN CASE
            WHEN p_audit_status = 'PENDING' THEN 'PENDING'
            WHEN p_audit_status = 'CHANGES_REQUESTED' THEN 'CHANGES_REQUESTED'
            WHEN p_audit_status = 'REJECTED' THEN 'BLOCKED'
            WHEN p_product_status = 'BLOCKED' THEN 'BLOCKED'
            WHEN COALESCE(p_stock, 0) <= 0 THEN 'SOLD_OUT'
            WHEN p_product_status = 'OFF_SHELF' THEN 'OFF_SHELF'
            WHEN p_product_status = 'NEEDS_REVISION' THEN 'NEEDS_REVISION'
            WHEN p_audit_status = 'APPROVED' AND p_product_status = 'ACTIVE' THEN 'ACTIVE'
            ELSE COALESCE(p_product_status, 'UNKNOWN')
        END
        """
    )
    op.execute(
        """
        CREATE FUNCTION fn_seller_trust_level(
            p_completed_orders INT,
            p_average_rating DECIMAL(4, 2),
            p_report_count INT
        )
        RETURNS VARCHAR(16)
        DETERMINISTIC
        NO SQL
        RETURN CASE
            WHEN COALESCE(p_completed_orders, 0) >= 10
             AND COALESCE(p_average_rating, 0) >= 4.70
             AND COALESCE(p_report_count, 0) <= 1
                THEN 'HIGH'
            WHEN COALESCE(p_completed_orders, 0) >= 3
             AND COALESCE(p_average_rating, 0) >= 4.30
             AND COALESCE(p_report_count, 0) <= 3
                THEN 'MEDIUM'
            ELSE 'LOW'
        END
        """
    )

    op.execute(
        """
        CREATE VIEW vw_active_product_catalog AS
        SELECT
            p.id AS id,
            p.seller_id AS seller_id,
            u.display_name AS seller_name,
            p.category_id AS category_id,
            c.name AS category_name,
            p.title AS title,
            p.description AS description,
            p.price AS price,
            p.stock AS stock,
            p.product_status AS product_status,
            p.audit_status AS audit_status,
            fn_product_display_status(p.audit_status, p.product_status, p.stock) AS display_status,
            p.tags AS tags,
            COALESCE(
                JSON_UNQUOTE(JSON_EXTRACT(p.tags, '$.hero_summary')),
                LEFT(p.description, 88)
            ) AS hero_summary,
            COALESCE(
                JSON_UNQUOTE(JSON_EXTRACT(p.tags, '$.condition_label')),
                JSON_UNQUOTE(JSON_EXTRACT(p.tags, '$.condition')),
                '成色良好'
            ) AS condition_label,
            JSON_UNQUOTE(JSON_EXTRACT(p.tags, '$.ship_from')) AS region_label,
            CASE
                WHEN p.audit_status = 'APPROVED' THEN '平台验真'
                ELSE '审核处理中'
            END AS verification_label,
            (
                SELECT pi.url
                FROM product_images pi
                WHERE pi.product_id = p.id
                ORDER BY pi.id ASC
                LIMIT 1
            ) AS cover_image,
            p.created_at AS created_at,
            p.updated_at AS updated_at
        FROM products p
        INNER JOIN users u ON u.id = p.seller_id
        LEFT JOIN categories c ON c.id = p.category_id
        """
    )
    op.execute(
        """
        CREATE VIEW vw_seller_operational_summary AS
        SELECT
            u.id AS seller_id,
            u.display_name AS seller_name,
            COALESCE(product_counts.total_products, 0) AS total_products,
            COALESCE(product_counts.active_products, 0) AS active_products,
            COALESCE(order_counts.completed_orders, 0) AS completed_orders,
            ROUND(COALESCE(review_counts.average_rating, 0), 1) AS average_rating,
            COALESCE(review_counts.review_count, 0) AS review_count,
            COALESCE(report_counts.report_count, 0) AS report_count,
            fn_seller_trust_level(
                COALESCE(order_counts.completed_orders, 0),
                COALESCE(review_counts.average_rating, 0),
                COALESCE(report_counts.report_count, 0)
            ) AS trust_level
        FROM users u
        LEFT JOIN (
            SELECT
                seller_id,
                COUNT(*) AS total_products,
                SUM(CASE WHEN product_status = 'ACTIVE' AND audit_status = 'APPROVED' THEN 1 ELSE 0 END) AS active_products
            FROM products
            GROUP BY seller_id
        ) AS product_counts ON product_counts.seller_id = u.id
        LEFT JOIN (
            SELECT seller_id, COUNT(*) AS completed_orders
            FROM orders
            WHERE status = 'COMPLETED'
            GROUP BY seller_id
        ) AS order_counts ON order_counts.seller_id = u.id
        LEFT JOIN (
            SELECT
                seller_id,
                AVG(rating) AS average_rating,
                COUNT(*) AS review_count
            FROM reviews
            WHERE review_type = 'SELLER'
            GROUP BY seller_id
        ) AS review_counts ON review_counts.seller_id = u.id
        LEFT JOIN (
            SELECT
                p.seller_id AS seller_id,
                COUNT(r.id) AS report_count
            FROM products p
            INNER JOIN reports r
                ON r.target_type = 'PRODUCT'
               AND r.target_id = p.id
            GROUP BY p.seller_id
        ) AS report_counts ON report_counts.seller_id = u.id
        WHERE u.is_admin = FALSE
        """
    )
    op.execute(
        """
        CREATE VIEW vw_admin_risk_overview AS
        SELECT
            COALESCE((SELECT COUNT(*) FROM reports WHERE status = 'PENDING'), 0) AS pending_reports,
            COALESCE((SELECT COUNT(*) FROM reports WHERE status = 'PROCESSED'), 0) AS processed_reports,
            COALESCE((SELECT COUNT(*) FROM appeals WHERE status = 'PENDING'), 0) AS pending_appeals,
            COALESCE((SELECT COUNT(*) FROM appeals WHERE status = 'APPROVED'), 0) AS approved_appeals,
            COALESCE((SELECT COUNT(*) FROM appeals WHERE status = 'REJECTED'), 0) AS rejected_appeals,
            COALESCE((SELECT COUNT(*) FROM audit_tasks WHERE status = 'PENDING'), 0) AS pending_audit_tasks,
            COALESCE((SELECT COUNT(*) FROM audit_tasks WHERE status = 'RUNNING'), 0) AS running_audit_tasks,
            COALESCE(
                (SELECT status FROM reports ORDER BY created_at DESC, id DESC LIMIT 1),
                'NONE'
            ) AS latest_report_status,
            COALESCE(
                (SELECT status FROM appeals ORDER BY created_at DESC, id DESC LIMIT 1),
                'NONE'
            ) AS latest_appeal_status
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_reports_after_insert_audit_task
        AFTER INSERT ON reports
        FOR EACH ROW
        INSERT INTO audit_tasks (
            task_type,
            entity_type,
            entity_id,
            status,
            payload,
            created_at,
            updated_at
        )
        SELECT
            'REPORT_REVIEW',
            'REPORT',
            NEW.id,
            'PENDING',
            JSON_OBJECT(
                'reason', NEW.reason,
                'target_type', NEW.target_type,
                'target_id', NEW.target_id,
                'source', 'trigger'
            ),
            UTC_TIMESTAMP(6),
            UTC_TIMESTAMP(6)
        WHERE NEW.status = 'PENDING'
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_reports_after_insert_operation_log
        AFTER INSERT ON reports
        FOR EACH ROW
        INSERT INTO operation_logs (
            actor_id,
            action,
            details,
            created_at,
            updated_at
        )
        SELECT
            NEW.reporter_id,
            'report.submit',
            JSON_OBJECT(
                'report_id', NEW.id,
                'target_type', NEW.target_type,
                'target_id', NEW.target_id,
                'source', 'trigger'
            ),
            UTC_TIMESTAMP(6),
            UTC_TIMESTAMP(6)
        WHERE NEW.status = 'PENDING'
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_reports_after_insert_operation_log")
    op.execute("DROP TRIGGER IF EXISTS trg_reports_after_insert_audit_task")
    op.execute("DROP VIEW IF EXISTS vw_admin_risk_overview")
    op.execute("DROP VIEW IF EXISTS vw_seller_operational_summary")
    op.execute("DROP VIEW IF EXISTS vw_active_product_catalog")
    op.execute("DROP FUNCTION IF EXISTS fn_seller_trust_level")
    op.execute("DROP FUNCTION IF EXISTS fn_product_display_status")

    op.drop_index("ix_reviews_product_created_at", table_name="reviews")
    op.drop_index("ix_audit_tasks_entity_status_created_at", table_name="audit_tasks")
    op.drop_index("ix_reports_status_created_at", table_name="reports")
    op.drop_index("ix_orders_buyer_status_created_at", table_name="orders")
    op.drop_index("ix_products_category_status_price", table_name="products")
    op.drop_index("ix_products_audit_status_product_status_updated_at", table_name="products")

    op.drop_constraint("uq_reviews_order_review_type", "reviews", type_="unique")
    op.drop_constraint("ck_order_items_quantity_positive", "order_items", type_="check")
    op.drop_constraint("ck_reviews_rating_range", "reviews", type_="check")
    op.drop_constraint("ck_products_stock_non_negative", "products", type_="check")
    op.drop_constraint("ck_products_price_non_negative", "products", type_="check")
