import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from unittest.mock import patch, Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.frontend import router
from services.auth_logic import check_session_exists
from utils.exceptions import AuthenticationError
from utils.exception_handlers import authentication_error_handler


def build_app():
    # mirror main.py: the AuthenticationError handler is app-level because
    # dependencies raise before any route body can catch it
    app = FastAPI()
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.include_router(router)
    return app


def test_get_url_authenticated():
    app = build_app()
    # override the session dependency so the test never hits Supabase
    app.dependency_overrides[check_session_exists] = lambda: {"id": "user-123", "access_token": "fake-token"}
    # patch at the point of use in the route so no real client/DB call happens
    with patch("routes.frontend.get_supabase_client_with_token") as mock_get_client, \
         patch("routes.frontend.get_url_from_supabase", return_value="https://example.com/chat") as mock_get_url, \
         patch("routes.frontend.get_published_status_from_supabase", return_value=True) as mock_get_published:
        mock_get_client.return_value = Mock()
        with TestClient(app) as client:
            response = client.get("/get-url")
    mock_get_client.assert_called_once_with("fake-token")
    mock_get_url.assert_called_once()
    mock_get_published.assert_called_once()
    assert response.status_code == 200
    assert response.json() == {"url": "https://example.com/chat", "published": True}


def test_set_publish_authenticated():
    app = build_app()
    app.dependency_overrides[check_session_exists] = lambda: {"id": "user-123", "access_token": "fake-token"}
    with TestClient(app) as client:
        response = client.post("/set-publish", json={"published": True})
    assert response.status_code == 200
    assert response.json() == {}


def test_get_url_unauthenticated():
    app = build_app()
    with TestClient(app) as client:
        # no Authorization header -> check_session_exists raises AuthenticationError(401)
        response = client.get("/get-url")
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing bearer token"}
