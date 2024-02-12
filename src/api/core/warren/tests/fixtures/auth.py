"""Fixtures for the authorization headers of warren api."""

import pytest

from ...utils import forge_lti_token


@pytest.fixture
def auth_headers() -> dict:
    """Generate authentication headers with a JWT token.

    This fixture generates authentication headers for use in testing scenarios.
    It creates a JWT token with predefined LTI parameters and returns it in
    the 'Authorization' header format.

    Returns:
        dict: A dictionary containing the 'Authorization' header with the JWT token.

    Example:
        To use this fixture in a test function, you can do the following::

            def test_authenticated_request(client):
                headers = auth_headers()
                response = client.get("/protected/resource", headers=headers)
                assert response.status_code == 200

    """
    return {"Authorization": f"Bearer {forge_lti_token()}"}
