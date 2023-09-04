"""Warren utils."""
import logging
from functools import reduce
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from typing_extensions import Annotated  # python <3.9 compat

from .conf import settings
from .models import LTIToken

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
