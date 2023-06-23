"""Warren LTI app URLs configuration."""

from django.urls import path

from .views import LTIRequestView

app_name = "lti"

urlpatterns = [
    path("", LTIRequestView.as_view(), name="lti-request-view"),
]
