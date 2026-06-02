from sqlalchemy import inspect, text


def test_alembic_upgrade_creates_core_tables(mysql_engine):
    inspector = inspect(mysql_engine)
    table_names = set(inspector.get_table_names())

    assert {"alembic_version", "users", "products", "orders", "reports"}.issubset(table_names)


def test_alembic_upgrade_creates_advanced_database_objects(mysql_engine):
    inspector = inspect(mysql_engine)

    view_names = set(inspector.get_view_names())
    assert {
        "vw_active_product_catalog",
        "vw_seller_operational_summary",
        "vw_admin_risk_overview",
    }.issubset(view_names)

    with mysql_engine.connect() as connection:
        routines = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT routine_name
                    FROM information_schema.routines
                    WHERE routine_schema = DATABASE()
                    """
                )
            ).all()
        }
        triggers = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT trigger_name
                    FROM information_schema.triggers
                    WHERE trigger_schema = DATABASE()
                    """
                )
            ).all()
        }
        indexes = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT DISTINCT index_name
                    FROM information_schema.statistics
                    WHERE table_schema = DATABASE()
                      AND index_name IN (
                        'ix_products_audit_status_product_status_updated_at',
                        'ix_products_category_status_price',
                        'ix_orders_buyer_status_created_at',
                        'ix_reports_status_created_at',
                        'ix_audit_tasks_entity_status_created_at',
                        'ix_reviews_product_created_at'
                      )
                    """
                )
            ).all()
        }
        constraints = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_schema = DATABASE()
                      AND constraint_name IN (
                        'ck_products_price_non_negative',
                        'ck_products_stock_non_negative',
                        'ck_reviews_rating_range',
                        'ck_order_items_quantity_positive',
                        'uq_reviews_order_review_type'
                      )
                    """
                )
            ).all()
        }

    assert {"fn_product_display_status", "fn_seller_trust_level"}.issubset(routines)
    assert {
        "trg_reports_after_insert_audit_task",
        "trg_reports_after_insert_operation_log",
    }.issubset(triggers)
    assert {
        "ix_products_audit_status_product_status_updated_at",
        "ix_products_category_status_price",
        "ix_orders_buyer_status_created_at",
        "ix_reports_status_created_at",
        "ix_audit_tasks_entity_status_created_at",
        "ix_reviews_product_created_at",
    }.issubset(indexes)
    assert {
        "ck_products_price_non_negative",
        "ck_products_stock_non_negative",
        "ck_reviews_rating_range",
        "ck_order_items_quantity_positive",
        "uq_reviews_order_review_type",
    }.issubset(constraints)
