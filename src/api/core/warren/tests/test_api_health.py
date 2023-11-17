"""Tests for the health check endpoints."""
import pytest
from ralph.backends.http.base import HTTPBackendStatus

from warren.api import health
from warren.backends import lrs_client


@pytest.mark.anyio
async def test_api_health_lbheartbeat(http_client):
    """Test the load balancer heartbeat healthcheck."""
    response = await http_client.get("/__lbheartbeat__")
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.anyio
async def test_api_health_heartbeat(http_client, monkeypatch):
    """Test the heartbeat healthcheck."""

    async def lrs_ok():
        return HTTPBackendStatus.OK

    async def lrs_away():
        return HTTPBackendStatus.AWAY

    async def lrs_error():
        return HTTPBackendStatus.ERROR

    with monkeypatch.context() as lrs_context:
        lrs_context.setattr(lrs_client, "status", lrs_ok)
        response = await http_client.get("/__heartbeat__")
        assert response.status_code == 200
        assert response.json() == {"database": "ok", "lrs": "ok"}

        lrs_context.setattr(lrs_client, "status", lrs_away)
        response = await http_client.get("/__heartbeat__")
        assert response.json() == {"database": "ok", "lrs": "away"}
        assert response.status_code == 500

        lrs_context.setattr(lrs_client, "status", lrs_error)
        response = await http_client.get("/__heartbeat__")
        assert response.json() == {"database": "ok", "lrs": "error"}
        assert response.status_code == 500

    with monkeypatch.context() as db_context:
        lrs_context.setattr(lrs_client, "status", lrs_ok)
        db_context.setattr(health, "is_db_alive", lambda: False)
        response = await http_client.get("/__heartbeat__")
        assert response.json() == {"database": "error", "lrs": "ok"}
        assert response.status_code == 500

        db_context.setattr(lrs_client, "status", lrs_away)
        response = await http_client.get("/__heartbeat__")
        assert response.json() == {"database": "error", "lrs": "away"}
        assert response.status_code == 500

        db_context.setattr(lrs_client, "status", lrs_error)
        response = await http_client.get("/__heartbeat__")
        assert response.json() == {"database": "error", "lrs": "error"}
        assert response.status_code == 500
