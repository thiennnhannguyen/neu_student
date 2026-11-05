import pytest
from flask import redirect

from app import create_app
from app.common.errors import ApiError


def assert_error_shape(response, status, code):
    assert response.status_code == status
    assert response.is_json
    body = response.get_json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "details"}
    assert body["error"]["code"] == code
    assert body["error"]["message"]
    assert isinstance(body["error"]["details"], dict)
    return body["error"]


def test_unknown_route_returns_404(client):
    assert_error_shape(client.get("/api/khong-ton-tai"), 404, "NOT_FOUND")


def test_wrong_method_returns_405(client):
    error = assert_error_shape(client.post("/api/health"), 405, "METHOD_NOT_ALLOWED")
    assert "GET" in error["details"]["allowed_methods"]


@pytest.mark.parametrize("config_name", ["testing", "development"])
def test_unexpected_error_returns_500_without_stack_trace(config_name):
    app = create_app(config_name)

    @app.get("/api/_boom")
    def boom():
        raise RuntimeError("bi-mat-noi-bo /duong/dan/file.py")

    response = app.test_client().get("/api/_boom")

    error = assert_error_shape(response, 500, "INTERNAL_ERROR")
    text = response.get_data(as_text=True)
    assert error["details"] == {}
    assert "bi-mat-noi-bo" not in text
    assert "Traceback" not in text
    assert "file.py" not in text


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (400, "BAD_REQUEST"),
        (401, "UNAUTHENTICATED"),
        (403, "FORBIDDEN"),
        (404, "NOT_FOUND"),
        (409, "CONFLICT"),
        (422, "VALIDATION_ERROR"),
    ],
)
def test_api_error_uses_standard_format(app, status, code):
    @app.get("/api/_fail")
    def fail():
        raise ApiError(status, details={"field": "x"})

    error = assert_error_shape(app.test_client().get("/api/_fail"), status, code)
    assert error["details"] == {"field": "x"}


def test_redirect_is_not_converted_to_error(app):
    @app.get("/api/_co-gach/")
    def with_slash():
        return redirect("/api/health")

    response = app.test_client().get("/api/_co-gach")

    assert response.status_code == 308
