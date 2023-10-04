"""Tokens for the LTI app."""

from django.conf import settings
from lti_toolbox.lti import LTI
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class LTITokenMixin:
    """Mixin class for creating a token payload from an LTI request.

    This mixin provides a method to instantiate a token class
    and update its payload with LTI information.
    """

    @classmethod
    def from_lti(cls, lti_request: LTI, lti_user: dict, session_id: str):
        """Instantiate a token class and update its payload with LTI data."""
        token = cls()
        token.payload.update(
            {
                "session_id": session_id,
                "roles": lti_request.roles,
                "user": lti_user,
                "locale": lti_request.get_param("launch_presentation_locale"),
                "resource_link_id": lti_request.get_param("resource_link_id"),
                "resource_link_description": lti_request.get_param(
                    "resource_link_description"
                ),
                # todo - determine whether the lis_result_sourcedid is useful.
            }
        )
        return token


class LTIAccessToken(LTITokenMixin, AccessToken):
    """LTI Access Token class.

    This class represents an access token used in the LTI integration.
    It includes LTI-specific information in its payload.
    """

    token_type = "lti_access"  # noqa: S105


class LTIRefreshToken(LTITokenMixin, RefreshToken):
    """LTI Refresh Token class.

    This class represents a refresh token used in the LTI integration.
    It includes LTI-specific information in its payload
    and is associated with an access token.
    """

    access_token_class = LTIAccessToken
    access_token_type = LTIAccessToken.token_type


class LTIContentItemSelectionToken(AccessToken):
    """LTI Content-Item Selection Token class.

    This class represents an access token used in the LTI deep-linking
    process. It ensures secure communication between the select and
    respond views by signing LTI parameters and validating their integrity.
    """

    token_type = "lti_access_content_item_selection"  # noqa: S105
    lifetime = settings.LTI_ACCESS_TOKEN_LIFETIME

    select_form_data_key = "lti_select_form_data"

    @classmethod
    def from_dict(cls, lti_select_form_data: dict):
        """Create a token instance from a dictionary of LTI parameters."""
        token = cls()
        token.payload[cls.select_form_data_key] = lti_select_form_data
        return token

    def verify(self):
        """Verify the token's integrity with additional checks.

        Raises:
            TokenError: If the token is malformed and does not contain
                            the expected data.
        """
        super().verify()
        if self.select_form_data_key not in self.payload:
            raise TokenError("Malformed LTI select form token")

    @property
    def lti_select_form_data(self):
        """Retrieve 'select_form_data_key' stored data from the token."""
        return self.payload.get(self.select_form_data_key)
