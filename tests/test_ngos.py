"""Testes dos endpoints /ngos do ngo-service."""
import psycopg2
import pytest


# ---------------------------------------------------------------------------
# GET /ngos
# ---------------------------------------------------------------------------
def test_get_ngos_returns_200(client):
    """GET /ngos retorna lista (mesmo que vazia) e status 200."""
    test_client, mocks = client
    mocks["cursor"].fetchall.return_value = [
        {
            "id": 1,
            "name": "Anjos de Patas",
            "email": "contato@anjosdepatas.org",
            "cause": "Proteção Animal",
            "city": "Osasco",
        },
    ]

    response = test_client.get("/ngos")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Anjos de Patas"


def test_get_ngos_empty_list(client):
    """GET /ngos com banco vazio retorna lista vazia."""
    test_client, mocks = client
    mocks["cursor"].fetchall.return_value = []

    response = test_client.get("/ngos")

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_ngos_db_error_returns_500(client):
    """Erro no banco retorna 500."""
    test_client, mocks = client
    mocks["cursor"].execute.side_effect = Exception("DB down")

    response = test_client.get("/ngos")

    assert response.status_code == 500
    assert "error" in response.get_json()


# ---------------------------------------------------------------------------
# POST /ngos
# ---------------------------------------------------------------------------
def test_create_ngo_success(client):
    """POST /ngos com payload válido retorna 201 e o objeto criado."""
    test_client, mocks = client
    mocks["cursor"].fetchone.return_value = {
        "id": 1,
        "name": "Educa Mais",
        "email": "info@educamais.org",
        "cause": "Educação",
        "city": "São Paulo",
    }

    payload = {
        "name": "Educa Mais",
        "email": "info@educamais.org",
        "cause": "Educação",
        "city": "São Paulo",
    }
    response = test_client.post("/ngos", json=payload)

    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 1
    assert data["name"] == "Educa Mais"
    # Garante que o commit foi chamado
    mocks["conn"].commit.assert_called_once()


@pytest.mark.parametrize(
    "missing_field",
    ["name", "email", "cause", "city"],
)
def test_create_ngo_missing_required_field_returns_400(client, missing_field):
    """Falta de qualquer campo obrigatório retorna 400."""
    test_client, _ = client
    full_payload = {
        "name": "Teste",
        "email": "t@t.org",
        "cause": "Causa",
        "city": "Cidade",
    }
    full_payload.pop(missing_field)

    response = test_client.post("/ngos", json=full_payload)

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_ngo_no_body_returns_400(client):
    """POST /ngos sem body retorna 400."""
    test_client, _ = client
    response = test_client.post(
        "/ngos",
        data="",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_create_ngo_duplicate_email_returns_409(client):
    """E-mail duplicado (UNIQUE constraint) retorna 409."""
    test_client, mocks = client
    mocks["cursor"].execute.side_effect = psycopg2.IntegrityError(
        "duplicate key value violates unique constraint"
    )

    payload = {
        "name": "Anjos",
        "email": "duplicado@ong.org",
        "cause": "X",
        "city": "Y",
    }
    response = test_client.post("/ngos", json=payload)

    assert response.status_code == 409
    # Garante que rollback foi chamado em vez de commit
    mocks["conn"].rollback.assert_called_once()
    mocks["conn"].commit.assert_not_called()
