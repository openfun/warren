"""Views for the dashboard app."""
from django.views.generic import TemplateView


class DashboardView(TemplateView):
    """Dummy dashboard view."""

    template_name = "dashboards/base.html"

    def _build_app_data(self):
        return {"key": "woop."}

    def get_context_data(self):
        """Enrich view's context with app's data."""
        parent_context = super().get_context_data()
        return {"app_data": self._build_app_data(), **parent_context}
