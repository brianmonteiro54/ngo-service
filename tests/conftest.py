"""
Configuração compartilhada do pytest para o ngo-service.

Patcha o pool de conexões PostgreSQL ANTES de importar a app,
para que os testes não precisem de banco real rodando.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest


# Variável de ambiente necessária para a app inicializar
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://fake:fake@localhost:5432/fake_db",
)


@pytest.fixture
def mock_pool():
    """Cria um mock do pool de conexões PostgreSQL."""
    pool_mock = MagicMock()
    conn_mock = MagicMock()
    cursor_mock = MagicMock()

    # Encadeamento: pool.getconn() → conn → conn.cursor() → cursor (context manager)
    pool_mock.getconn.return_value = conn_mock
    conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
    conn_mock.cursor.return_value.__exit__.return_value = False

    return {
        "pool": pool_mock,
        "conn": conn_mock,
        "cursor": cursor_mock,
    }


@pytest.fixture
def client(mock_pool):
    """Cria um test client Flask com o pool mockado."""
    # Patcha SimpleConnectionPool ANTES de importar a app
    with patch("psycopg2.pool.SimpleConnectionPool", return_value=mock_pool["pool"]):
        # Reimporta para que o patch entre em vigor
        if "app" in sys.modules:
            del sys.modules["app"]
        import app as app_module

        # Injeta o pool mockado também na variável global do módulo,
        # caso a app já tenha sido importada antes em outro teste
        app_module.pool = mock_pool["pool"]

        with app_module.app.test_client() as c:
            yield c, mock_pool
