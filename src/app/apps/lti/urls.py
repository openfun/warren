"""Warren LTI app URLs configuration."""

from django.urls import path

from .views import LTIConfigView, LTIRequestView

app_name = "lti"

urlpatterns = [
    path("", LTIRequestView.as_view(), name="lti-request-view"),
    path("config.xml", LTIConfigView.as_view(), name="lti-config-view"),
]
