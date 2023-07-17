"""Tests for the development app."""

from django.test import TestCase, override_settings


@override_settings(DEBUG=True)
class DevelopmentLTIViewTest(TestCase):
    """Test the development view."""

    def test_development_route(self):
        """The development app has a route that answers."""
        response = self.client.get("/development/")
        self.assertEqual(response.status_code, 200)
