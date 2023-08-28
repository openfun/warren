"""Warren LTI app URLs configuration."""

from django.urls import path

from .views import LTIConfigView, LTIRequestView, LTIRespondView, LTISelectView

app_name = "lti"

urlpatterns = [
    path("<str:selection>/", LTIRequestView.as_view(), name="lti-request-view"),
    path("config.xml", LTIConfigView.as_view(), name="lti-config-view"),
    path("select", LTISelectView.as_view(), name="lti-select-view"),
    path("respond", LTIRespondView.as_view(), name="lti-respond-view"),
]
