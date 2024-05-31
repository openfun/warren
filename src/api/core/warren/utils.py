"""Warren utils."""

import datetime
import logging
import uuid
from functools import reduce
from typing import Callable, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from lti_toolbox.launch_params import LTIRole
from pydantic import ValidationError
from typing_extensions import Annotated  # python <3.9 compat

from .conf import settings
from .models import LTIToken, LTIUser

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def pipe(*functions: Callable) -> Callable:
    """Create a functions pipeline.

    Note that functions are applied in the order they are passed to the
    function (first one first).

    Example usage:

    # Given `a()`, `b()` and `c()` defined functions
    output = pipe(a, b, c)(input)

    """
    return reduce(lambda f, g: lambda x: g(f(x)), functions, lambda x: x)


def get_lti_token(token: Annotated[str, Depends(oauth2_scheme)]) -> LTIToken:
    """Get the JWT, decode its payload and verify its signature."""
    try:
        payload = LTIToken.parse_obj(
            jwt.decode(
                token,
                settings.APP_SIGNING_KEY,
                algorithms=[settings.APP_SIGNING_ALGORITHM],
            )
        )
    except JWTError as exception:
        message = "Could not validate credentials"
        logger.error("%s: %s", message, exception)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exception
    except ValidationError as exception:
        message = "An error occurred while validating the token"
        logger.error("%s: %s", message, exception)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
        ) from exception

    return payload


def get_lti_course_id(lti_token: Annotated[LTIToken, Depends(get_lti_token)]) -> str:
    """Get the course id from the LTI token."""
    return lti_token.course_id


def get_lti_user_id(lti_token: Annotated[LTIToken, Depends(get_lti_token)]) -> str:
    """Get the user id from the LTI token."""
    return lti_token.user.id


def get_lti_roles(
    lti_token: Annotated[LTIToken, Depends(get_lti_token)]
) -> List[LTIRole]:
    """Check if user is an instructor from the LTI token."""
    return lti_token.roles


JOHN_DOE_USER = LTIUser(
    id="johndoe",
    email="johndoe@example.com",
)


def forge_lti_token(  # noqa: PLR0913
    user: LTIUser = JOHN_DOE_USER,
    roles: tuple = ("instructor",),
    consumer_site: str = "http://fake-lms.com",
    course_id: str = "course-v1:openfun+mathematics101+session01",
    locale: str = "fr",
    resource_link_id: str = "",
    resource_link_description: str = "",
) -> str:
    """Forge a LTI token to use for the CLI."""
    timestamp = int(datetime.datetime.now().timestamp())
    lti_parameters = LTIToken(
        token_type="lti_access",  # noqa: S106
        exp=timestamp + 10000,
        iat=timestamp,
        jti="",
        session_id=str(uuid.uuid4()),
        consumer_site=consumer_site,
        course_id=course_id,
        roles=roles,
        user=user,
        locale=locale,
        resource_link_id=resource_link_id,
        resource_link_description=resource_link_description,
    )

    token = jwt.encode(
        lti_parameters.dict(),
        settings.APP_SIGNING_KEY,
        algorithm=settings.APP_SIGNING_ALGORITHM,
    )
    return token
