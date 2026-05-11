from fastapi.testclient import TestClient

from app.sessions import SESSION_COOKIE
from app.main import app


def test_session_cookie_is_issued_and_reused() -> None:
    client = TestClient(app)

    first = client.get("/api/session")
    second = client.get("/api/session")

    assert first.status_code == 200
    assert second.status_code == 200
    assert SESSION_COOKIE in first.cookies
    assert first.json()["operatorKey"] == second.json()["operatorKey"]
    assert first.json()["source"] == "session-cookie"


def test_trusted_header_takes_precedence_over_cookie() -> None:
    client = TestClient(app)

    response = client.get("/api/session", headers={"X-Auth-Request-Email": "User.Name@example.com"})

    assert response.status_code == 200
    assert response.json()["operatorKey"] == "user-user.name@example.com"
    assert response.json()["source"] == "trusted-header"
