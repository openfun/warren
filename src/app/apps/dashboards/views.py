from django.views.generic import TemplateView


class DashboardView(TemplateView):
    """Dummy dashboard view"""

    template_name = "dashboards/base.html"
