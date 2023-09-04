"""Fixtures for the authorization headers of warren api."""
import datetime
import uuid

import pytest
from jose import jwt

from ...conf import settings
from ...models import LTIToken, LTIUser


@pytest.fixture
def auth_headers():
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
    lti_user = LTIUser(
        platform="http://fake-lms.com",
        course="course-v1:openfun+mathematics101+session01",
        email="johndoe@example.com",
        user="johndoe",
    )
    timestamp = int(datetime.datetime.now().timestamp())
    lti_parameters = LTIToken(
        token_type="lti_access",  # noqa: S106
        exp=timestamp + 10000,
        iat=timestamp,
        jti="",
        session_id=str(uuid.uuid4()),
        roles=["instrucgtor"],
        user=lti_user,
        locale="fr",
        resource_link_id="8d5dabc2-6af4-42ac-a29b-97649db4a162",
        resource_link_description="",
    )

    token = jwt.encode(
        lti_parameters.dict(),
        settings.APP_SIGNING_KEY,
        algorithm=settings.APP_SIGNING_ALGORITHM,
    )

    return {"Authorization": f"Bearer {token}"}
