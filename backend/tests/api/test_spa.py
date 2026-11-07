"""Phục vụ bản build: tệp tĩnh, đường dẫn React Router, ranh giới với API, đi ngược thư mục."""

import pytest

from app import create_app
from app.blueprints.spa import NO_BUILD_MESSAGE

INDEX_HTML = "<!doctype html><title>NEU</title>"


@pytest.fixture
def dist(tmp_path):
    folder = tmp_path / "dist"
    (folder / "assets").mkdir(parents=True)
    (folder / "index.html").write_text(INDEX_HTML, encoding="utf8")
    (folder / "assets" / "app.js").write_text("console.log(1)", encoding="utf8")
    (tmp_path / "bi-mat.txt").write_text("bi mat", encoding="utf8")
    return folder


@pytest.fixture
def spa_client(dist):
    return create_app("testing", {"FRONTEND_DIST": str(dist)}).test_client()


@pytest.mark.parametrize("path", ["/", "/login", "/m11/ket-qua", "/m12/dinh-huong/nghe/ai"])
def test_page_paths_return_index_without_login(spa_client, path):
    response = spa_client.get(path)

    assert response.status_code == 200
    assert response.get_data(as_text=True) == INDEX_HTML
    assert response.mimetype == "text/html"


def test_asset_is_served(spa_client):
    response = spa_client.get("/assets/app.js")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "console.log(1)"


@pytest.mark.parametrize("path", ["/assets/thieu.js", "/assets/thieu", "/thieu.png"])
def test_missing_file_is_json_404_not_html(spa_client, path):
    response = spa_client.get(path)

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
@pytest.mark.parametrize("path", ["/api", "/api/", "/api/khong-ton-tai", "/api/m11/khong"])
def test_unknown_api_path_never_gets_the_spa(spa_client, method, path):
    response = getattr(spa_client, method)(path, headers={"X-Requested-With": "fetch"})

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


def test_path_starting_with_api_but_not_api_folder_is_a_page(spa_client):
    assert spa_client.get("/apidocs").get_data(as_text=True) == INDEX_HTML


@pytest.mark.parametrize(
    "path", ["/../bi-mat.txt", "/assets/../../bi-mat.txt", "/%2e%2e/bi-mat.txt", "/..%2fbi-mat.txt"]
)
def test_cannot_read_outside_dist(spa_client, path):
    response = spa_client.get(path)

    assert "bi mat" not in response.get_data(as_text=True)


def test_missing_build_says_what_to_do(tmp_path):
    client = create_app("testing", {"FRONTEND_DIST": str(tmp_path / "khong")}).test_client()

    for path in ("/", "/login", "/assets/app.js"):
        response = client.get(path)
        assert response.status_code == 503
        assert NO_BUILD_MESSAGE in response.get_data(as_text=True)
        assert "make build" in response.get_data(as_text=True)


def test_health_still_answers_json(spa_client):
    assert spa_client.get("/api/health").status_code == 200
