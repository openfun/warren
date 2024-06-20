"""Tests for the development app."""

from django.test import TestCase, override_settings


@override_settings(DEBUG=True)
class DevelopmentLTIViewTest(TestCase):
    """Test the development view."""

    def test_development_routes(self):
        """The development app has routes that answers."""
        response = self.client.get("/development/select")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/development/request")
        self.assertEqual(response.status_code, 200)
