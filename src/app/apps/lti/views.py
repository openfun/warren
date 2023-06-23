"""Views for the LTI app."""

import logging
from urllib.parse import urlencode, urlparse

from django.core import signing
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from lti_toolbox.exceptions import LTIException
from lti_toolbox.lti import LTI
from lti_toolbox.views import BaseLTIView

from .forms import BaseLTIUserForm, SignedLTIUserForm

logger = logging.getLogger(__name__)


class LTIRequestView(BaseLTIView):
    """Base view to handle LTI launch request verification."""

    def _do_on_success(self, lti_request: LTI) -> HttpResponse:
        """Redirect to the target view."""
        lti_user = {
            "platform": lti_request.get_consumer().url,
            "course": lti_request.get_param("context_id"),
            "user": lti_request.get_param("lis_person_sourcedid"),
            "email": lti_request.get_param("lis_person_contact_email_primary"),
        }

        lti_user_form = BaseLTIUserForm(lti_user)
        if not lti_user_form.is_valid():
            logger.debug("LTI user is not valid: %s", lti_user_form.errors)
            raise PermissionDenied

        return redirect("dashboards:dashboard-view")

    def _do_on_failure(self, request: HttpRequest, error: LTIException) -> HttpResponse:
        """Raise an error when the LTI request fails."""
        logger.debug("LTI request failed with error: %s", error)
        raise PermissionDenied
