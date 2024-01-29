"""Tests for Warren db module."""

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session as SASession

from warren.db import is_alive


def test_db_is_alive(monkeypatch):
    """Test the database is_alive status check."""
    assert is_alive() is True

    def raise_operational_error(*args, **kwargs):
        raise OperationalError(None, None, None)

    monkeypatch.setattr(SASession, "execute", raise_operational_error)
    assert is_alive() is False
