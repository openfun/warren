"""Views for the LTI app."""

import json
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin, TemplateView
from lti_toolbox.exceptions import LTIException
from lti_toolbox.lti import LTI
from lti_toolbox.views import BaseLTIView

from .forms import BaseLTIUserForm

logger = logging.getLogger(__name__)


class RenderMixins(TemplateResponseMixin):
    """Mixin class for rendering an LTI view with app_data.

    This mixin provides the necessary template to render the frontend
    while passing app_data through the DOM. By calling the 'render' method,
    the app_data is constructed. The default value for app_data is an
    empty dictionary, which can be overridden in your subclass.

    Attributes:
        template_name (str): The name of the template to be used for rendering.
        app_data (dict): Data passed to the frontend. Default is an empty dict.
    """

    template_name = "base.html"
    app_data = {}

    def render_to_response(self, context=None, **response_kwargs):
        """Render view's template with app's data dumped in JSON string.

        Returns:
            HttpResponse: The HTTP response containing the rendered template.
        """
        if context is None:
            context = {}

        context["app_data"] = json.dumps(self.app_data)
        return super().render_to_response(context, **response_kwargs)


class LTIRequestView(BaseLTIView, RenderMixins):
    """Base view to handle LTI launch request verification."""

    def _do_on_success(self, lti_request: LTI) -> HttpResponse:
        """Build the App's data and render the LTI view."""
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

        self.app_data = {"key": "woop."}

        return self.render()

    def _do_on_failure(self, request: HttpRequest, error: LTIException) -> HttpResponse:
        """Handle LTI request failure by raising a PermissionDenied error."""
        logger.debug("LTI request failed with error: %s", error)
        raise PermissionDenied


class LTIConfigView(TemplateView):
    """Provide access to Warren LTI Provider Configurations for Consumers.

    For instance, when configuring an LMS like Moodle, you have the ability to provide
    a URL for the LTI tool configurations of the provider. This function returns an
    XML containing a set of predefined LTI parameters that may need to be
    overloaded manually.
    """

    template_name = "config.xml"
    content_type = "text/xml; charset=utf-8"

    def get_context_data(self, **kwargs):
        """Get context data for rendering the template."""
        return {
            "code": settings.LTI_CONFIG_TITLE.lower()
            if settings.LTI_CONFIG_TITLE
            else None,
            "contact_email": settings.LTI_CONFIG_CONTACT_EMAIL,
            "description": settings.LTI_CONFIG_DESCRIPTION,
            "host": self.request.get_host(),
            "icon_url": settings.LTI_CONFIG_ICON,
            "title": settings.LTI_CONFIG_TITLE,
            "url": settings.LTI_CONFIG_URL,
        }
