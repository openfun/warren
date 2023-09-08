"""Tests for the LTI respond view."""


import json
from logging import Logger
from unittest import mock

from django.test import TestCase
from lti_toolbox.factories import LTIConsumerFactory, LTIPassportFactory
from lti_toolbox.models import LTIPassport
from lti_toolbox.utils import sign_parameters


class LTIRespondViewTestCase(TestCase):
    """Test the LTI respond view."""

    def setUp(self):
        """Set up an LTI consumer and passport for the tests."""
        super().setUp()
        self._consumer = LTIConsumerFactory(
            slug="test_lti", title="test consumer", url="http://testserver.com"
        )
        self._passport = LTIPassportFactory(
            title="test passport", consumer=self._consumer
        )

    def test_views_lti_respond_valid(self):
        """Validate the response's format returned by the view."""
        lti_select_form_data = {
            "content_item_return_url": "http://testserver.com/lti/select",
        }

        signed_parameters = sign_parameters(
            self._passport, lti_select_form_data, "http://testserver.com/lti/select"
        )

        signed_parameters.update({"selection": "demo"})

        response = self.client.post(
            "/lti/respond",
            signed_parameters,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<html>")

        context = response.context_data

        self.assertEqual(
            context.get("form_action"),
            signed_parameters.get("content_item_return_url"),
        )

        form_data = context.get("form_data")
        for key, value in signed_parameters.items():
            if "oauth" in key or key == "content_item_return_url":
                continue

            self.assertEqual(value, form_data.get(key))

        self.assertContains(response, "oauth_consumer_key")
        self.assertContains(response, "oauth_signature")
        self.assertContains(response, "oauth_nonce")

        self.assertEqual(
            json.dumps(
                {
                    "@context": "http://purl.imsglobal.org/ctx/lti/v1/ContentItem",
                    "@graph": [
                        {
                            "@type": "ContentItem",
                            "url": "http://testserver/lti/demo/",
                            "frame": [],
                        }
                    ],
                }
            ),
            form_data.get("content_items"),
        )

        self.assertEqual(
            signed_parameters.get("oauth_consumer_key"),
            form_data.get("oauth_consumer_key"),
        )
        self.assertNotEqual(
            signed_parameters.get("oauth_signature"),
            form_data.get("oauth_signature"),
        )

    @mock.patch.object(Logger, "debug")
    def test_views_lti_respond_missing_selection(self, mock_logger):
        """Validate that view fails when the selection is missing."""
        lti_select_form_data = {
            "content_item_return_url": "http://testserver.com/lti/select",
        }

        signed_parameters = sign_parameters(
            self._passport, lti_select_form_data, "http://testserver.com/lti/select"
        )

        response = self.client.post(
            "/lti/respond",
            signed_parameters,
        )
        self.assertEqual(response.status_code, 400)
        mock_logger.assert_called_with("LTI response failed with error: no selection")

    @mock.patch(
        "oauthlib.oauth1.rfc5849.generate_nonce",
        return_value="59474787080480293391616018589",
    )
    @mock.patch("oauthlib.oauth1.rfc5849.generate_timestamp", return_value="1616018589")
    def test_views_lti_respond_verify_signature(self, mock_timestamp, mock_nonce):
        """Validate that view signs correctly its response."""
        mocked_passport = LTIPassport(
            title="test_generate_keys_on_save_p2",
            consumer=self._consumer,
            oauth_consumer_key="custom_consumer_key",
            shared_secret="random_shared_secret",  # noqa: S106
        )
        mocked_passport.save()

        lti_select_form_data = {
            "content_item_return_url": "http://testserver.com/lti/select",
        }

        signed_parameters = sign_parameters(
            mocked_passport, lti_select_form_data, "http://testserver.com/lti/select"
        )

        signed_parameters.update({"selection": "demo"})

        response = self.client.post(
            "/lti/respond",
            signed_parameters,
        )
        context = response.context_data
        form_data = context.get("form_data")

        self.assertEqual(mock_timestamp.return_value, form_data.get("oauth_timestamp"))
        self.assertEqual(mock_nonce.return_value, form_data.get("oauth_nonce"))
        self.assertEqual(
            "9Nn4MRLzOLV4/tSWzQwMGttG60Y=", form_data.get("oauth_signature")
        )

    @mock.patch.object(Logger, "debug")
    def test_views_lti_respond_missing_content_item_return_url(self, mock_logger):
        """Validate that view fails when the content_item_return_url is missing."""
        lti_select_form_data = {}

        signed_parameters = sign_parameters(
            self._passport, lti_select_form_data, "http://testserver.com/lti/select"
        )

        signed_parameters.update({"selection": "demo"})

        response = self.client.post(
            "/lti/respond",
            signed_parameters,
        )
        self.assertEqual(response.status_code, 400)
        mock_logger.assert_called_with(
            "LTI response failed with error: missing content-item return url"
        )
