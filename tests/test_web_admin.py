from collections import OrderedDict

import pytest
from dotenv import dotenv_values

from config import Config
from core.shopping_list import ShoppingListService
from frontends.web_admin import create_admin_app


class FakeWhatsAppClient:
    def __init__(self):
        self.is_connected = True
        self.qr_data_uri = None
        self.allowed_chat_jid = "123@g.us"
        self.seen_chats = OrderedDict({"123@g.us": "2026-01-01 10:00:00"})


@pytest.fixture
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("ALLOWED_CHAT_JID=123@g.us\n", encoding="utf-8")
    return str(path)


@pytest.fixture
def service():
    service = ShoppingListService(":memory:")
    service.add_items(["חלב"])
    return service


@pytest.fixture
def app(service, env_file):
    config = Config(db_path=":memory:", session_path="data/session.db", allowed_chat_jid="123@g.us")
    return create_admin_app(config, FakeWhatsAppClient(), service, env_path=env_file)


def test_dashboard_shows_status_config_and_list(app):
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Connected" in body
    assert "123@g.us" in body
    assert "חלב" in body


def test_add_item_via_the_web_form(app, service):
    client = app.test_client()
    response = client.post("/list/add", data={"text": "לחם, ביצים"})
    assert response.status_code == 302
    pending, _ = service.get_list()
    assert "לחם" in pending and "ביצים" in pending


def test_toggle_checkbox_marks_item_collected(app, service):
    client = app.test_client()
    client.post("/list/toggle", data={"name": "חלב", "checked": "on"})
    pending, collected = service.get_list()
    assert pending == [] and collected == ["חלב"]


def test_toggle_checkbox_unmarks_item(app, service):
    service.mark_collected(["חלב"])
    client = app.test_client()
    client.post("/list/toggle", data={"name": "חלב"})  # unchecked: no "checked" field
    pending, collected = service.get_list()
    assert pending == ["חלב"] and collected == []


def test_remove_item_via_the_web_button(app, service):
    client = app.test_client()
    client.post("/list/remove", data={"name": "חלב"})
    pending, collected = service.get_list()
    assert pending == [] and collected == []


def test_clear_list_via_the_web_button(app, service):
    client = app.test_client()
    client.post("/list/clear")
    pending, collected = service.get_list()
    assert pending == [] and collected == []


def test_logs_endpoint_returns_no_logs_message_when_file_missing(app, tmp_path, monkeypatch):
    monkeypatch.setattr("frontends.web_admin._LOG_FILE", str(tmp_path / "missing.log"))
    client = app.test_client()
    response = client.get("/logs")
    assert response.status_code == 200
    assert response.get_json()["logs"] == "No logs yet."


def test_status_endpoint_reports_connection_and_qr_state():
    fake_client = FakeWhatsAppClient()
    fake_client.is_connected = False
    fake_client.qr_data_uri = "data:image/png;base64,abc"
    service = ShoppingListService(":memory:")
    config = Config(db_path=":memory:", session_path="data/session.db", allowed_chat_jid="")
    app = create_admin_app(config, fake_client, service, env_path="unused.env")

    response = app.test_client().get("/status")
    body = response.get_json()
    assert body["connected"] is False
    assert body["qr_data_uri"] == "data:image/png;base64,abc"


def test_save_writes_new_values_to_env_file(app, env_file, monkeypatch):
    monkeypatch.setattr("frontends.web_admin._reboot", lambda: None)
    client = app.test_client()
    response = client.post(
        "/save",
        data={
            "ALLOWED_CHAT_JID": "999@g.us",
            "DB_PATH": "data/shopping_list.db",
            "SESSION_PATH": "data/session.db",
            "ADMIN_PORT": "8080",
        },
    )
    assert response.status_code == 200
    saved = dotenv_values(env_file)
    assert saved["ALLOWED_CHAT_JID"] == "999@g.us"
    assert saved["ADMIN_PORT"] == "8080"
