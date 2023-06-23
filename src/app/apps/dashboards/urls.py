"""Warren dashboards app URLs configuration."""

from django.urls import path

from .views import DashboardView

app_name = "dashboards"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard-view"),
]
