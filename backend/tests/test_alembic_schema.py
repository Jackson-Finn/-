from sqlalchemy import inspect


def test_alembic_upgrade_creates_core_tables(mysql_engine):
    inspector = inspect(mysql_engine)
    table_names = set(inspector.get_table_names())

    assert {"alembic_version", "users", "products", "orders", "reports"}.issubset(table_names)
