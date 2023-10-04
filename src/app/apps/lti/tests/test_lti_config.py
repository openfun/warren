"""Tests for the LTI configuration view."""


import xmltodict
from django.test import TestCase


class LTIConfigViewTestCase(TestCase):
    """Test LTI configuration view."""

    def test_views_lti_config_xml_cartridge(self):
        """Validate that xml hardcoded cartridge data is correctly rendered."""
        response = self.client.get("/lti/config.xml")
        self.assertEqual(response.status_code, 200)

        received_cartridge_data = xmltodict.parse(response.content)[
            "cartridge_basiclti_link"
        ]

        expected_cartridge_data = {
            "@xmlns": "http://www.imsglobal.org/xsd/imslticc_v1p0",
            "@xmlns:blti": "http://www.imsglobal.org/xsd/imsbasiclti_v1p0",
            "@xmlns:lticm": "http://www.imsglobal.org/xsd/imslticm_v1p0",
            "@xmlns:lticp": "http://www.imsglobal.org/xsd/imslticp_v1p0",
            "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "@xsi:schemaLocation": "http://www.imsglobal.org/xsd/imslticc_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticc_v1p0.xsd     http://www.imsglobal.org/xsd/imsbasiclti_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imsbasiclti_v1p0.xsd     http://www.imsglobal.org/xsd/imslticm_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticm_v1p0.xsd     http://www.imsglobal.org/xsd/imslticp_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticp_v1p0.xsd",  # noqa: E501 pylint: disable=line-too-long
        }

        for key, expected_value in expected_cartridge_data.items():
            self.assertEqual(received_cartridge_data[key], expected_value)

    def test_views_lti_config_strings(self):
        """Validate that xml is correctly rendered."""
        mocked_settings = {
            "LTI_CONFIG_TITLE": "Test",
            "LTI_CONFIG_DESCRIPTION": "This is a test.",
            "LTI_CONFIG_CONTACT_EMAIL": "contact@example.com",
            "LTI_CONFIG_ICON": "test-icon.png",
            "LTI_CONFIG_URL": "https://example.com",
        }

        with self.settings(**mocked_settings):
            response = self.client.get("/lti/config.xml")
            self.assertEqual(response.status_code, 200)

            self.assertEqual(
                response.context_data,
                {
                    "code": "test",
                    "contact_email": "contact@example.com",
                    "description": "This is a test.",
                    "host": "testserver",
                    "icon_scheme_relative_url": "//testserver/static/test-icon.png",
                    "title": "Test",
                    "url": "https://example.com",
                },
            )

            self.assertEqual(response["Content-Type"], "text/xml; charset=utf-8")

            received_cartridge_data = xmltodict.parse(response.content)[
                "cartridge_basiclti_link"
            ]
            expected_vendor = {
                "lticp:code": "test",
                "lticp:name": "Test",
                "lticp:description": "This is a test.",
                "lticp:url": "https://example.com",
                "lticp:contact": {"lticp:email": "contact@example.com"},
            }

            self.assertEqual(received_cartridge_data["blti:vendor"], expected_vendor)

            expected_data = {
                "blti:title": "Test",
                "blti:description": "This is a test.",
                "blti:launch_url": "http://testserver",
                "blti:secure_launch_url": "https://testserver",
                "blti:icon": "http://testserver/static/test-icon.png",
                "blti:secure_icon": "https://testserver/static/test-icon.png",
            }

            for key, expected_value in expected_data.items():
                self.assertEqual(received_cartridge_data[key], expected_value)

    def test_views_lti_config_empty_strings(self):
        """Validate that xml is correctly rendered when config are empty."""
        mocked_settings = {
            "LTI_CONFIG_TITLE": "",
            "LTI_CONFIG_DESCRIPTION": "",
            "LTI_CONFIG_CONTACT_EMAIL": "",
            "LTI_CONFIG_ICON": "",
            "LTI_CONFIG_URL": "",
        }

        with self.settings(**mocked_settings):
            response = self.client.get("/lti/config.xml")
            self.assertEqual(response.status_code, 200)

            self.assertEqual(
                response.context_data,
                {
                    "code": None,
                    "contact_email": "",
                    "description": "",
                    "host": "testserver",
                    "icon_scheme_relative_url": "",
                    "title": "",
                    "url": "",
                },
            )

            self.assertEqual(response["Content-Type"], "text/xml; charset=utf-8")

            received_cartridge_data = xmltodict.parse(response.content)[
                "cartridge_basiclti_link"
            ]

            expected_data = {
                "blti:launch_url": "http://testserver",
                "blti:secure_launch_url": "https://testserver",
            }

            for key, expected_value in expected_data.items():
                self.assertEqual(received_cartridge_data[key], expected_value)

            for key in [
                "blti:description",
                "blti:title",
                "blti:icon",
                "blti:secure_icon",
                "blti:vendor",
            ]:
                self.assertFalse(key in received_cartridge_data)

    def test_views_lti_config_none(self):
        """Validate that xml is correctly rendered when config are None."""
        mocked_settings = {
            "LTI_CONFIG_TITLE": None,
            "LTI_CONFIG_DESCRIPTION": None,
            "LTI_CONFIG_CONTACT_EMAIL": None,
            "LTI_CONFIG_ICON": None,
            "LTI_CONFIG_URL": None,
        }

        with self.settings(**mocked_settings):
            response = self.client.get("/lti/config.xml")
            self.assertEqual(response.status_code, 200)

            self.assertEqual(
                response.context_data,
                {
                    "code": None,
                    "contact_email": None,
                    "description": None,
                    "host": "testserver",
                    "icon_scheme_relative_url": "",
                    "title": None,
                    "url": None,
                },
            )

            self.assertEqual(response["Content-Type"], "text/xml; charset=utf-8")

            received_cartridge_data = xmltodict.parse(response.content)[
                "cartridge_basiclti_link"
            ]

            expected_data = {
                "blti:launch_url": "http://testserver",
                "blti:secure_launch_url": "https://testserver",
            }

            for key, expected_value in expected_data.items():
                self.assertEqual(received_cartridge_data[key], expected_value)

            # Optional LTI configurations should not be present.
            for key in [
                "blti:description",
                "blti:title",
                "blti:icon",
                "blti:secure_icon",
                "blti:vendor",
            ]:
                self.assertFalse(key in received_cartridge_data)

    def test_views_lti_config_one_vendor_config(self):
        """Validate that xml is correctly rendered when only one config is given."""
        mocked_settings = {
            "LTI_CONFIG_TITLE": "",
            "LTI_CONFIG_DESCRIPTION": "",
            "LTI_CONFIG_CONTACT_EMAIL": "contact@example.com",
            "LTI_CONFIG_ICON": "",
            "LTI_CONFIG_URL": "",
        }

        with self.settings(**mocked_settings):
            response = self.client.get("/lti/config.xml")
            self.assertEqual(response.status_code, 200)

            self.assertEqual(
                response.context_data,
                {
                    "code": None,
                    "contact_email": "contact@example.com",
                    "description": "",
                    "host": "testserver",
                    "icon_scheme_relative_url": "",
                    "title": "",
                    "url": "",
                },
            )

            self.assertEqual(response["Content-Type"], "text/xml; charset=utf-8")

            received_cartridge_data = xmltodict.parse(response.content)[
                "cartridge_basiclti_link"
            ]

            expected_data = {
                "blti:launch_url": "http://testserver",
                "blti:secure_launch_url": "https://testserver",
            }

            self.assertTrue(expected_data.items() <= received_cartridge_data.items())

            for key in [
                "blti:description",
                "blti:title",
                "blti:icon",
                "blti:secure_icon",
            ]:
                self.assertFalse(key in received_cartridge_data)

            expected_vendor = {
                "lticp:contact": {"lticp:email": "contact@example.com"},
            }

            self.assertEqual(received_cartridge_data["blti:vendor"], expected_vendor)

    def test_views_lti_config_default(self):
        """Validate that xml is correctly rendered with default values."""
        response = self.client.get("/lti/config.xml")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context_data,
            {
                "code": "warren",
                "contact_email": None,
                "description": (
                    "An opensource visualization platform for learning analytics."
                ),
                "host": "testserver",
                "icon_scheme_relative_url": "//testserver/static/warren_52x52.svg",
                "title": "Warren",
                "url": None,
            },
        )

        self.assertEqual(response["Content-Type"], "text/xml; charset=utf-8")

        received_cartridge_data = xmltodict.parse(response.content)[
            "cartridge_basiclti_link"
        ]

        expected_data = {
            "blti:launch_url": "http://testserver",
            "blti:secure_launch_url": "https://testserver",
            "blti:description": (
                "An opensource visualization platform for learning analytics."
            ),
        }

        self.assertTrue(expected_data.items() <= received_cartridge_data.items())
