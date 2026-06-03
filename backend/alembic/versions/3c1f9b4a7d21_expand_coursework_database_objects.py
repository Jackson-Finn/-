"""expand coursework database objects

Revision ID: 3c1f9b4a7d21
Revises: 8d4bf17961d5
Create Date: 2026-06-03 10:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3c1f9b4a7d21"
down_revision: Union[str, Sequence[str], None] = "8d4bf17961d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "governance_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_label", sa.String(length=120), nullable=False),
        sa.Column("pending_reports", sa.Integer(), nullable=False),
        sa.Column("processed_reports", sa.Integer(), nullable=False),
        sa.Column("pending_appeals", sa.Integer(), nullable=False),
        sa.Column("approved_appeals", sa.Integer(), nullable=False),
        sa.Column("rejected_appeals", sa.Integer(), nullable=False),
        sa.Column("pending_audit_tasks", sa.Integer(), nullable=False),
        sa.Column("governance_priority", sa.String(length=16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_governance_snapshots_captured_at",
        "governance_snapshots",
        ["captured_at"],
        unique=False,
    )
    op.create_index(
        "ix_governance_snapshots_snapshot_label",
        "governance_snapshots",
        ["snapshot_label"],
        unique=False,
    )

    op.execute("DROP EVENT IF EXISTS ev_capture_admin_risk_snapshot")
    op.execute("DROP TRIGGER IF EXISTS trg_appeals_after_insert_audit_task")
    op.execute("DROP TRIGGER IF EXISTS trg_appeals_after_insert_operation_log")
    op.execute("DROP PROCEDURE IF EXISTS sp_create_report_case")
    op.execute("DROP PROCEDURE IF EXISTS sp_capture_admin_risk_snapshot")
    op.execute("DROP FUNCTION IF EXISTS fn_governance_priority")
    op.execute("DROP FUNCTION IF EXISTS fn_seller_quality_band")

    op.execute(
        """
        CREATE FUNCTION fn_governance_priority(
            p_pending_reports INT,
            p_pending_appeals INT,
            p_pending_audit_tasks INT
        )
        RETURNS VARCHAR(16)
        DETERMINISTIC
        NO SQL
        RETURN CASE
            WHEN COALESCE(p_pending_audit_tasks, 0) >= 4 OR COALESCE(p_pending_reports, 0) >= 3 THEN 'HIGH'
            WHEN COALESCE(p_pending_audit_tasks, 0) >= 2 OR COALESCE(p_pending_reports, 0) >= 1 OR COALESCE(p_pending_appeals, 0) >= 1 THEN 'MEDIUM'
            ELSE 'LOW'
        END
        """
    )
    op.execute(
        """
        CREATE FUNCTION fn_seller_quality_band(
            p_average_rating DECIMAL(4, 2),
            p_review_count INT
        )
        RETURNS VARCHAR(16)
        DETERMINISTIC
        NO SQL
        RETURN CASE
            WHEN COALESCE(p_review_count, 0) >= 10 AND COALESCE(p_average_rating, 0) >= 4.8 THEN 'PREMIUM'
            WHEN COALESCE(p_review_count, 0) >= 5 AND COALESCE(p_average_rating, 0) >= 4.5 THEN 'TRUSTED'
            WHEN COALESCE(p_review_count, 0) >= 1 THEN 'GROWING'
            ELSE 'NEW'
        END
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW vw_seller_operational_summary AS
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
            ) AS trust_level,
            fn_seller_quality_band(
                COALESCE(review_counts.average_rating, 0),
                COALESCE(review_counts.review_count, 0)
            ) AS quality_band
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
        CREATE OR REPLACE VIEW vw_admin_risk_overview AS
        SELECT
            COALESCE((SELECT COUNT(*) FROM reports WHERE status = 'PENDING'), 0) AS pending_reports,
            COALESCE((SELECT COUNT(*) FROM reports WHERE status = 'PROCESSED'), 0) AS processed_reports,
            COALESCE((SELECT COUNT(*) FROM appeals WHERE status = 'PENDING'), 0) AS pending_appeals,
            COALESCE((SELECT COUNT(*) FROM appeals WHERE status = 'APPROVED'), 0) AS approved_appeals,
            COALESCE((SELECT COUNT(*) FROM appeals WHERE status = 'REJECTED'), 0) AS rejected_appeals,
            COALESCE((SELECT COUNT(*) FROM audit_tasks WHERE status = 'PENDING'), 0) AS pending_audit_tasks,
            COALESCE((SELECT COUNT(*) FROM audit_tasks WHERE status = 'RUNNING'), 0) AS running_audit_tasks,
            fn_governance_priority(
                COALESCE((SELECT COUNT(*) FROM reports WHERE status = 'PENDING'), 0),
                COALESCE((SELECT COUNT(*) FROM appeals WHERE status = 'PENDING'), 0),
                COALESCE((SELECT COUNT(*) FROM audit_tasks WHERE status = 'PENDING'), 0)
            ) AS governance_priority,
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
        CREATE OR REPLACE VIEW vw_latest_governance_snapshot AS
        SELECT
            id,
            snapshot_label,
            pending_reports,
            processed_reports,
            pending_appeals,
            approved_appeals,
            rejected_appeals,
            pending_audit_tasks,
            governance_priority,
            payload,
            captured_at,
            created_at,
            updated_at
        FROM governance_snapshots
        WHERE id = (
            SELECT MAX(inner_snapshots.id)
            FROM governance_snapshots AS inner_snapshots
        )
        """
    )

    op.execute(
        """
        CREATE PROCEDURE sp_create_report_case(
            IN p_reporter_id INT,
            IN p_target_type VARCHAR(64),
            IN p_target_id INT,
            IN p_reason TEXT
        )
        INSERT INTO reports (
            reporter_id,
            target_type,
            target_id,
            reason,
            status,
            decision,
            created_at,
            updated_at
        )
        VALUES (
            p_reporter_id,
            p_target_type,
            p_target_id,
            p_reason,
            'PENDING',
            NULL,
            UTC_TIMESTAMP(6),
            UTC_TIMESTAMP(6)
        )
        """
    )
    op.execute(
        """
        CREATE PROCEDURE sp_capture_admin_risk_snapshot(
            IN p_snapshot_label VARCHAR(120)
        )
        INSERT INTO governance_snapshots (
            snapshot_label,
            pending_reports,
            processed_reports,
            pending_appeals,
            approved_appeals,
            rejected_appeals,
            pending_audit_tasks,
            governance_priority,
            payload,
            captured_at,
            created_at,
            updated_at
        )
        SELECT
            COALESCE(NULLIF(p_snapshot_label, ''), 'manual'),
            pending_reports,
            processed_reports,
            pending_appeals,
            approved_appeals,
            rejected_appeals,
            pending_audit_tasks,
            governance_priority,
            JSON_OBJECT(
                'pending_reports', pending_reports,
                'processed_reports', processed_reports,
                'pending_appeals', pending_appeals,
                'approved_appeals', approved_appeals,
                'rejected_appeals', rejected_appeals,
                'pending_audit_tasks', pending_audit_tasks,
                'governance_priority', governance_priority,
                'latest_report_status', latest_report_status,
                'latest_appeal_status', latest_appeal_status
            ),
            UTC_TIMESTAMP(6),
            UTC_TIMESTAMP(6),
            UTC_TIMESTAMP(6)
        FROM vw_admin_risk_overview
        LIMIT 1
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_appeals_after_insert_audit_task
        AFTER INSERT ON appeals
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
            'APPEAL_REVIEW',
            'APPEAL',
            NEW.id,
            'PENDING',
            JSON_OBJECT(
                'reason', NEW.reason,
                'report_id', NEW.report_id,
                'source', 'trigger'
            ),
            UTC_TIMESTAMP(6),
            UTC_TIMESTAMP(6)
        WHERE NEW.status = 'PENDING'
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_appeals_after_insert_operation_log
        AFTER INSERT ON appeals
        FOR EACH ROW
        INSERT INTO operation_logs (
            actor_id,
            action,
            details,
            created_at,
            updated_at
        )
        SELECT
            NEW.applicant_id,
            'appeal.submit',
            JSON_OBJECT(
                'appeal_id', NEW.id,
                'report_id', NEW.report_id,
                'source', 'trigger'
            ),
            UTC_TIMESTAMP(6),
            UTC_TIMESTAMP(6)
        WHERE NEW.status = 'PENDING'
        """
    )

    op.execute(
        """
        CREATE EVENT ev_capture_admin_risk_snapshot
        ON SCHEDULE EVERY 1 DAY
        STARTS CURRENT_TIMESTAMP + INTERVAL 1 DAY
        ON COMPLETION PRESERVE
        ENABLE
        DO
            CALL sp_capture_admin_risk_snapshot('event-daily')
        """
    )


def downgrade() -> None:
    op.execute("DROP EVENT IF EXISTS ev_capture_admin_risk_snapshot")
    op.execute("DROP TRIGGER IF EXISTS trg_appeals_after_insert_operation_log")
    op.execute("DROP TRIGGER IF EXISTS trg_appeals_after_insert_audit_task")
    op.execute("DROP PROCEDURE IF EXISTS sp_capture_admin_risk_snapshot")
    op.execute("DROP PROCEDURE IF EXISTS sp_create_report_case")
    op.execute("DROP VIEW IF EXISTS vw_latest_governance_snapshot")

    op.execute(
        """
        CREATE OR REPLACE VIEW vw_seller_operational_summary AS
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
        CREATE OR REPLACE VIEW vw_admin_risk_overview AS
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

    op.execute("DROP FUNCTION IF EXISTS fn_seller_quality_band")
    op.execute("DROP FUNCTION IF EXISTS fn_governance_priority")

    op.drop_index("ix_governance_snapshots_snapshot_label", table_name="governance_snapshots")
    op.drop_index("ix_governance_snapshots_captured_at", table_name="governance_snapshots")
    op.drop_table("governance_snapshots")
