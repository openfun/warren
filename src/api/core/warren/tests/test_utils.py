"""Test Warren utility functions."""
import datetime
import uuid
from logging import Logger
from unittest import mock

import pytest
from fastapi import HTTPException
from jose import jwt
from lti_toolbox.launch_params import LTIRole

from warren.utils import get_lti_token, pipe

from ..conf import settings


def test_pipe():
    """Test the pipe function."""

    def add(x):
        return x + 1

    def minus(x):
        return x - 2

    def mult(x):
        return x * 3

    assert pipe(add, minus, mult)(3) == 6
    assert pipe(add, mult)(2) == 9
    assert pipe(add)(1) == 2
    with pytest.raises(TypeError):
        pipe()()


def test_get_lti_token():
    """Test the get_lti_token function."""
    # Mock signing env variables
    settings.APP_SIGNING_KEY = "SigningKeyToChange__FOR_TEST_ONLY"
    settings.APP_SIGNING_ALGORITHM = "HS256"

    # Mock lti parameters
    lti_user = {
        "platform": "http://fake-lms.com",
        "course": "course-v1:openfun+mathematics101+session01",
        "email": "johndoe@example.com",
        "user": "johndoe",
    }
    timestamp = int(datetime.datetime.now().timestamp())
    expected_lti_parameters = {
        "token_type": "lti_access",
        "exp": timestamp + 10000,
        "iat": timestamp,
        "jti": "",
        "session_id": str(uuid.uuid4()),
        "roles": ["instructor"],
        "user": lti_user,
        "locale": "fr",
        "resource_link_id": "8d5dabc2-6af4-42ac-a29b-97649db4a162",
        "resource_link_description": "",
    }

    token = jwt.encode(
        expected_lti_parameters,
        settings.APP_SIGNING_KEY,
        algorithm=settings.APP_SIGNING_ALGORITHM,
    )

    # Decode token, verify its signature and validate its payload
    assert get_lti_token(token) == expected_lti_parameters


@mock.patch.object(Logger, "error")
def test_get_lti_token_invalid_signature(mock_logger):
    """Test the get_lti_token function with an invalid signature."""
    # Mock signing env variables
    settings.APP_SIGNING_KEY = "SigningKeyToChange__FOR_TEST_ONLY"
    settings.APP_SIGNING_ALGORITHM = "HS256"

    # Mock lti parameters
    lti_user = {
        "platform": "http://fake-lms.com",
        "course": "course-v1:openfun+mathematics101+session01",
        "email": "johndoe@example.com",
        "user": "johndoe",
    }
    timestamp = int(datetime.datetime.now().timestamp())
    lti_parameters = {
        "token_type": "lti_access",
        "exp": timestamp + 10000,
        "iat": timestamp,
        "jti": "",
        "session_id": str(uuid.uuid4()),
        "roles": ["instructor"],
        "user": lti_user,
        "locale": "fr",
        "resource_link_id": "8d5dabc2-6af4-42ac-a29b-97649db4a162",
        "resource_link_description": "",
    }

    # A wrong signing key is used to encode the token
    token = jwt.encode(
        lti_parameters, "WRONG_KEY", algorithm=settings.APP_SIGNING_ALGORITHM
    )

    # Token should not be valid
    with pytest.raises(HTTPException) as exception:
        get_lti_token(token)

    assert exception.value.status_code == 401
    assert str(exception.value.detail) == "Could not validate credentials"
    mock_logger.assert_called_with("%s: %s", "Could not validate credentials", mock.ANY)


@mock.patch.object(Logger, "error")
def test_get_lti_token_expired(mock_logger):
    """Test the get_lti_token function with an expired token."""
    # Mock signing env variables
    settings.APP_SIGNING_KEY = "SigningKeyToChange__FOR_TEST_ONLY"
    settings.APP_SIGNING_ALGORITHM = "HS256"

    # Mock lti parameters
    lti_user = {
        "platform": "http://fake-lms.com",
        "course": "course-v1:openfun+mathematics101+session01",
        "email": "johndoe@example.com",
        "user": "johndoe",
    }
    timestamp = int(datetime.datetime.now().timestamp())
    lti_parameters = {
        "token_type": "lti_access",
        "exp": timestamp - 10000,  # Make the token expire
        "iat": timestamp,
        "jti": "",
        "session_id": str(uuid.uuid4()),
        "roles": ["instructor"],
        "user": lti_user,
        "locale": "fr",
        "resource_link_id": "8d5dabc2-6af4-42ac-a29b-97649db4a162",
        "resource_link_description": "",
    }

    token = jwt.encode(
        lti_parameters,
        settings.APP_SIGNING_KEY,
        algorithm=settings.APP_SIGNING_ALGORITHM,
    )

    # Token should be expired
    with pytest.raises(HTTPException) as exception:
        get_lti_token(token)

    assert exception.value.status_code == 401
    assert str(exception.value.detail) == "Could not validate credentials"
    mock_logger.assert_called_with("%s: %s", "Could not validate credentials", mock.ANY)


@mock.patch.object(Logger, "error")
def test_get_lti_token_wrong_payload(mock_logger):
    """Test the get_lti_token function with an invalid payload."""
    # Mock signing env variables
    settings.APP_SIGNING_KEY = "SigningKeyToChange__FOR_TEST_ONLY"
    settings.APP_SIGNING_ALGORITHM = "HS256"

    # Mock lti parameters
    lti_user = {
        "platform": "http://fake-lms.com",
        "course": "course-v1:openfun+mathematics101+session01",
        "email": "johndoe@example.com",
        "user": "johndoe",
    }
    timestamp = int(datetime.datetime.now().timestamp())
    lti_parameters = {
        "token_type": "lti_access",
        "exp": timestamp + 10000,
        "iat": timestamp,
        "jti": "",
        "session_id": str(uuid.uuid4()),
        "roles": [LTIRole.INSTRUCTOR, "other-role"],
        "user": lti_user,
        "locale": "fr",
        "resource_link_id": None,  # Resource link id is missing
        "resource_link_description": None,
    }

    token = jwt.encode(
        lti_parameters,
        settings.APP_SIGNING_KEY,
        algorithm=settings.APP_SIGNING_ALGORITHM,
    )

    # Token's payload should be invalid
    with pytest.raises(HTTPException) as exception:
        get_lti_token(token)

    assert exception.value.status_code == 500
    assert str(exception.value.detail) == "An error occurred while validating the token"
    mock_logger.assert_called_with(
        "%s: %s", "An error occurred while validating the token", mock.ANY
    )
