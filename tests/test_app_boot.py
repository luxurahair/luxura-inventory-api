import importlib


def test_app_imports_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    session_module = importlib.import_module("app.db.session")

    assert str(session_module.engine.url).startswith("sqlite")


def test_wix_router_imports():
    wix_module = importlib.import_module("app.routes.wix")

    assert hasattr(wix_module, "router")
