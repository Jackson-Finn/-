from app.core.config import Settings


def test_default_database_url_is_mysql(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)
    assert (
        settings.database_url
        == "mysql+pymysql://marketplace:marketplace@127.0.0.1:3306/advanced_marketplace?charset=utf8mb4"
    )
