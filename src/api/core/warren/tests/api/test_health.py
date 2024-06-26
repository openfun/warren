"""Tests for the health check endpoints."""

import pytest
from ralph.backends.data.base import DataBackendStatus

from warren.api import health
from warren.backends import lrs_client
from warren.db import Session


@pytest.mark.anyio
async def test_api_health_lbheartbeat(http_client):
    """Test the load balancer heartbeat healthcheck."""
    response = await http_client.get("/__lbheartbeat__")
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.anyio
async def test_api_health_heartbeat(db_session, http_client, monkeypatch):
    """Test the heartbeat healthcheck."""
    monkeypatch.setattr(Session, "_session", db_session)

    async def lrs_ok():
        return DataBackendStatus.OK

    async def lrs_away():
        return DataBackendStatus.AWAY

    async def lrs_error():
        return DataBackendStatus.ERROR

    with monkeypatch.context() as lrs_context:
        lrs_context.setattr(lrs_client, "status", lrs_ok)
        response = await http_client.get("/__heartbeat__")
        assert response.status_code == 200
        assert response.json() == {"data": "ok", "lrs": "ok"}

        lrs_context.setattr(lrs_client, "status", lrs_away)
        response = await http_client.get("/__heartbeat__")
        assert response.json() == {"data": "ok", "lrs": "away"}
        assert response.status_code == 500

        lrs_context.setattr(lrs_client, "status", lrs_error)
        response = await http_client.get("/__heartbeat__")
        assert response.json() == {"data": "ok", "lrs": "error"}
        assert response.status_code == 500

    with monkeypatch.context() as db_context:
        lrs_context.setattr(lrs_client, "status", lrs_ok)
        db_context.setattr(health, "is_db_alive", lambda: False)
        response = await http_client.get("/__heartbeat__")
        assert response.json() == {"data": "error", "lrs": "ok"}
        assert response.status_code == 500

        db_context.setattr(lrs_client, "status", lrs_away)
        response = await http_client.get("/__heartbeat__")
        assert response.json() == {"data": "error", "lrs": "away"}
        assert response.status_code == 500

        db_context.setattr(lrs_client, "status", lrs_error)
        response = await http_client.get("/__heartbeat__")
        assert response.json() == {"data": "error", "lrs": "error"}
        assert response.status_code == 500
