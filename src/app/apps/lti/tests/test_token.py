"""Tests for the Token classes."""

from urllib.parse import urlencode

from django.test import RequestFactory, TestCase
from lti_toolbox.factories import LTIConsumerFactory, LTIPassportFactory
from lti_toolbox.lti import LTI
from lti_toolbox.utils import CONTENT_TYPE, sign_parameters

from ..token import LTIRefreshToken


class LTISelectFormAccessTokenTestCase(TestCase):
    """Test the LTIRefreshToken class."""

    @classmethod
    def setUpClass(cls):
        """Provides test setup to create a verified LTI request."""
        super().setUpClass()

        cls.request_factory = RequestFactory()
        cls._consumer = LTIConsumerFactory(slug="test_lti")
        cls._passport = LTIPassportFactory(
            title="test passport", consumer=cls._consumer
        )
        cls._url = "http://testserver/lti/launch"

    def _verified_lti_request(self, lti_parameters):
        signed_parameters = sign_parameters(self._passport, lti_parameters, self._url)
        lti = self._lti_request(signed_parameters, self._url)
        lti.verify()
        return lti

    def _lti_request(self, signed_parameters, url):
        request = self.request_factory.post(
            url, data=urlencode(signed_parameters), content_type=CONTENT_TYPE
        )
        return LTI(request)

    def test_refresh_token_from_lti(self):
        """Validate that token can be created from an LTI request."""
        # Mock LTI request and user data
        lti_request = self._verified_lti_request(
            {
                "lti_message_type": "basic-lti-launch-request",
                "lti_version": "LTI-1p0",
                "resource_link_id": "df7",
                "context_id": "1",
                "user_id": "1",
                "lis_person_contact_email_primary": "contact@example.com",
                "roles": "Instructor",
            }
        )
        lti_user = {
            "user_id": 123,
            "username": "lti_user",
        }
        session_id = "session123"

        # Create an LTIRefreshToken instance from LTI data
        refresh_token = LTIRefreshToken.from_lti(lti_request, lti_user, session_id)

        # Assert that the refresh token is an instance of LTIRefreshToken
        self.assertIsInstance(refresh_token, LTIRefreshToken)

        # Assert that the payload of the refresh token contains the expected data
        expected_payload = {
            "token_type": "refresh",
            "session_id": session_id,
            "user": lti_user,
            "roles": ["instructor"],
            "locale": None,
            "resource_link_id": "df7",
            "resource_link_description": None,
        }
        self.assertTrue(expected_payload.items() <= refresh_token.payload.items())

        # Should not raise
        refresh_token.verify()
