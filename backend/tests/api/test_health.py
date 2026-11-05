def test_health_ok_without_login(client):
    """Thành công và "không đăng nhập": API công khai nên vẫn trả 200."""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "is_mock": True}
