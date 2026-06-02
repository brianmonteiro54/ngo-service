"""Testes do endpoint /health do ngo-service."""


def test_health_returns_200(client):
    """GET /health deve retornar 200 e status ok."""
    test_client, _ = client
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "ngo-service"


def test_health_is_json(client):
    """Resposta de /health deve ser application/json."""
    test_client, _ = client
    response = test_client.get("/health")

    assert response.content_type.startswith("application/json")
