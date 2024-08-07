"""Tests for the LTI request view."""

import json
import re
from html import unescape
from logging import Logger
from unittest import mock
from urllib.parse import urlencode

from django.test import TestCase, override_settings
from lti_toolbox.factories import LTIConsumerFactory, LTIPassportFactory
from lti_toolbox.utils import CONTENT_TYPE, sign_parameters

from ..token import LTIAccessToken, LTIRefreshToken

TARGET_URL_PATH = "/lti/test/"


class LTIRequestViewTestCase(TestCase):
    """Test the LTI request view."""

    def setUp(self):
        """Set up an LTI consumer and passport for the tests."""
        super().setUp()
        self._consumer = LTIConsumerFactory(
            slug="test_lti", title="test consumer", url="http://fake-lms.com/lms1/"
        )
        self._passport = LTIPassportFactory(
            title="test passport", consumer=self._consumer
        )

    @override_settings(ALLOWED_HOSTS=["fake-warren.com"])
    @mock.patch.object(Logger, "debug")
    def test_views_lti_request_invalid_request_type(self, mock_logger):
        """Validate that view fails when the LTI request type is a selection."""
        # Its type is not a basic launch request.
        lti_parameters = {
            "lti_message_type": "ContentItemSelectionRequest",
            "lti_version": "LTI-1p0",
            "accept_media_types": "application/vnd.ims.lti.v1.ltilink",
            "accept_presentation_document_targets": "frame,iframe,window",
            "content_item_return_url": "http://fake-lms.com/lms1/",
            "context_id": "1",
            "user_id": "1",
            "lis_person_contact_email_primary": "contact@example.com",
            "roles": "teacher",
        }

        signed_parameters = sign_parameters(
            self._passport,
            lti_parameters,
            f"http://fake-warren.com{TARGET_URL_PATH}",
        )

        response = self.client.post(
            TARGET_URL_PATH,
            urlencode(signed_parameters),
            content_type=CONTENT_TYPE,
            HTTP_HOST="fake-warren.com",
        )
        self.assertEqual(response.status_code, 403)
        mock_logger.assert_called_with("LTI message type is not valid")

    @override_settings(ALLOWED_HOSTS=["fake-warren.com", "wrongserver.com"])
    @mock.patch.object(Logger, "info")
    def test_views_lti_request_invalid_signature(self, mock_logger):
        """Validate that view fails when the LTI signature is invalid."""
        lti_parameters = {
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": "df7",
        }

        signed_parameters = sign_parameters(
            self._passport, lti_parameters, f"http://fake-warren.com{TARGET_URL_PATH}"
        )

        # The POST request is initiated from a distinct host compared to
        # the one that's responsible for signing its payload.
        response = self.client.post(
            TARGET_URL_PATH,
            urlencode(signed_parameters),
            content_type=CONTENT_TYPE,
            HTTP_HOST="wrongserver.com",
        )
        self.assertEqual(response.status_code, 403)
        mock_logger.assert_called_with("Valid signature: %s", False)

    @override_settings(ALLOWED_HOSTS=["fake-warren.com"])
    @mock.patch.object(Logger, "debug")
    def test_views_lti_request_invalid_user(self, mock_logger):
        """Validate that view fails when the LTI user is invalid."""
        # LTI user information are missing.
        lti_parameters = {
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": "df7",
            "context_id": "course-v1:openfun+mathematics101+session01",
        }

        signed_parameters = sign_parameters(
            self._passport, lti_parameters, f"http://fake-warren.com{TARGET_URL_PATH}"
        )

        response = self.client.post(
            TARGET_URL_PATH,
            urlencode(signed_parameters),
            content_type=CONTENT_TYPE,
            HTTP_HOST="fake-warren.com",
        )
        self.assertEqual(response.status_code, 403)
        mock_logger.assert_called_with(
            "LTI user is not valid: %s",
            {
                "id": ["Ce champ est obligatoire."],
                "email": ["Ce champ est obligatoire."],
            },
        )

    @override_settings(
        ALLOWED_HOSTS=["fake-warren.com"],
        STORAGES={
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        },
    )
    def test_views_lti_request_valid_edx(self):
        """Validate that view is correctly rendered."""
        lti_parameters = {
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": "df7",
            "context_id": "course-v1:openfun+mathematics101+session01",
            "context_title": "Mathematics 101",
            "user_id": "1",
            "lis_person_contact_email_primary": "contact@example.com",
            "roles": "teacher",
        }

        signed_parameters = sign_parameters(
            self._passport, lti_parameters, f"http://fake-warren.com{TARGET_URL_PATH}"
        )

        response = self.client.post(
            TARGET_URL_PATH,
            urlencode(signed_parameters),
            content_type=CONTENT_TYPE,
            HTTP_HOST="fake-warren.com",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<html>")

        # Get the context data passed to the frontend from the DOM
        match = re.search(
            '<div id="warren-frontend-data" data-context="(.*)"></div>',
            response.content.decode("utf-8"),
        )

        # Load its json content
        context = json.loads(unescape(match.group(1)))

        # Check that the frontend would route to the 'test' route
        self.assertEqual(context["lti_route"], "test")

        # Check that the frontend would receive course and context info
        self.assertEqual(context["context_title"], "Mathematics 101")
        self.assertEqual(
            context["course_info"],
            {
                "organization": "openfun",
                "course_name": "mathematics101",
                "course_run": "session01",
            },
        )

        LTIRefreshToken(context["refresh"]).verify()
        LTIAccessToken(context["access"]).verify()

    @override_settings(
        ALLOWED_HOSTS=["fake-warren.com"],
        STORAGES={
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        },
    )
    def test_views_lti_request_valid_moodle(self):
        """Validate that view is correctly rendered."""
        lti_parameters = {
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": "df7",
            "context_id": "1234",
            "context_title": "Mathematics 101",
            "user_id": "1",
            "lis_person_contact_email_primary": "contact@example.com",
            "roles": "teacher",
            "tool_consumer_instance_name": "FUN",
            "tool_consumer_info_product_family_code": "moodle",
        }

        signed_parameters = sign_parameters(
            self._passport, lti_parameters, f"http://fake-warren.com{TARGET_URL_PATH}"
        )

        response = self.client.post(
            TARGET_URL_PATH,
            urlencode(signed_parameters),
            content_type=CONTENT_TYPE,
            HTTP_HOST="fake-warren.com",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<html>")

        # Get the context data passed to the frontend from the DOM
        match = re.search(
            '<div id="warren-frontend-data" data-context="(.*)"></div>',
            response.content.decode("utf-8"),
        )

        # Load its json content
        context = json.loads(unescape(match.group(1)))

        # Check that the frontend would route to the 'test' route
        self.assertEqual(context["lti_route"], "test")

        # Check that the frontend would receive course and context info
        self.assertEqual(context["context_title"], "Mathematics 101")
        self.assertEqual(
            context["course_info"],
            {
                "organization": "FUN",
                "course_name": "Mathematics 101",
                "course_run": None,
            },
        )

        LTIRefreshToken(context["refresh"]).verify()
        LTIAccessToken(context["access"]).verify()
