"""Warren Development app URLs configuration."""

from django.urls import path

from .views import DevelopmentLTIRequestView, DevelopmentLTISelectView

app_name = "development"

urlpatterns = [
    path(
        "development/request",
        DevelopmentLTIRequestView.as_view(),
        name="lti-request-view",
    ),
    path(
        "development/select",
        DevelopmentLTISelectView.as_view(),
        name="lti-select-view",
    ),
]
