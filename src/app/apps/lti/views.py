"""Views for the LTI app."""

import json
import logging
import uuid
from urllib.parse import unquote

from django.conf import settings
from django.core.exceptions import BadRequest, PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin, TemplateView
from lti_toolbox.exceptions import LTIException
from lti_toolbox.launch_params import LTIMessageType
from lti_toolbox.lti import LTI
from lti_toolbox.models import LTIPassport
from lti_toolbox.views import BaseLTIView
from oauthlib import oauth1

from .forms import BaseLTIUserForm
from .token import LTIRefreshToken

logger = logging.getLogger(__name__)


class TokenMixin:
    """Mixin class for handling token generation from an LTI request.

    This mixin provides methods to parse user data from an LTI request
    and generate access and refresh tokens.
    """

    def parse_user_data(self, lti_request: LTI):
        """Parse user data from the given LTI request and validate it."""
        lti_user_data = {
            "platform": lti_request.get_consumer().url,
            "course": lti_request.get_param("context_id"),
            "user": lti_request.get_param("lis_person_sourcedid"),
            "email": lti_request.get_param("lis_person_contact_email_primary"),
        }
        lti_user_form = BaseLTIUserForm(lti_user_data)
        if not lti_user_form.is_valid():
            logger.debug("LTI user is not valid: %s", lti_user_form.errors)
            raise PermissionDenied

        return lti_user_data

    def generate_tokens(self, lti_request: LTI):
        """Generate access and refresh tokens using the parsed LTI user data."""
        lti_user_data = self.parse_user_data(lti_request)

        session_id = str(uuid.uuid4())
        refresh_token = LTIRefreshToken.from_lti(lti_request, lti_user_data, session_id)

        return {
            "access": str(refresh_token.access_token),
            "refresh": str(refresh_token),
        }


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


class LTIRequestView(BaseLTIView, RenderMixins, TokenMixin):
    """Base view to handle LTI launch request verification."""

    def _do_on_success(self, lti_request: LTI, *args, **kwargs) -> HttpResponse:
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

        if lti_request.get_param("lti_message_type") != LTIMessageType.LAUNCH_REQUEST:
            logger.debug("LTI message type is not valid")
            raise PermissionDenied

        jwt = self.generate_tokens(lti_request)
        self.app_data = {"lti_route": kwargs["selection"] or "demo", **jwt}

        return self.render_to_response()

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


@method_decorator(csrf_exempt, name="dispatch")
class LTISelectView(BaseLTIView, RenderMixins, TokenMixin):
    """View to handle LTI Content-Item selection request.

    This view handles LTI Content-Item selection requests submitted in a deep linking
    context, typically by Moodle. The request enables the Tool Consumer (TC) to choose
    which resource will be displayed in the Learning Management System (LMS). This class
    verifies the request's validity and provides the necessary data to
    render a selection form.

    Attributes:
        Inherits attributes from BaseLTIView and RenderMixins.
    """

    def _do_on_success(self, lti_request: LTI) -> HttpResponse:
        """Build app data and render the LTI view based on a successful request."""
        jwt = self.generate_tokens(lti_request)

        lti_select_form_data = self.request.POST.copy()

        if lti_select_form_data["lti_message_type"] != LTIMessageType.SELECTION_REQUEST:
            logger.debug("LTI message type is not valid")
            raise PermissionDenied

        if not lti_request.can_edit_content:
            logger.debug("LTI role is not valid")
            raise PermissionDenied

        lti_select_form_data["lti_message_type"] = LTIMessageType.SELECTION_RESPONSE

        # todo - sign lti_select_form_data with an access token.

        self.app_data = {
            "lti_route": "select",
            "lti_select_form_action_url": reverse("lti:lti-respond-view"),
            "lti_select_form_data": lti_select_form_data,
            **jwt,
        }

        return self.render_to_response()

    def _do_on_failure(self, request: HttpRequest, error: LTIException) -> HttpResponse:
        """Handle LTI request failure by raising a PermissionDenied error."""
        logger.debug("LTI request failed with error: %s", error)
        raise PermissionDenied


@method_decorator(csrf_exempt, name="dispatch")
class LTIRespondView(TemplateResponseMixin, View):
    """View for handling the submission of LTI Content-Item selections.

    This view manages the submission of Content-Item selections from the frontend,
    sending them back to the return URL provided by the Learning Management System
    (LMS). It acts as an intermediary that validates the selection, renders a template
    to automatically submit a form, and triggers the auto-submission process.
    This form-based submission is currently the only viable method to pass Content-Item
    selections back to the LMS under the current version of the LTI protocol.
    """

    template_name = "autosubmit_form.html"

    def post(self, request, *args, **kwargs):
        """Handle the POST request for Content-Item selection submission."""
        # todo - decode lti_select_form_data from a signed token.
        lti_select_form_data = self.request.POST.copy()

        content_item_return_url = lti_select_form_data.get("content_item_return_url")

        if not content_item_return_url:
            logger.debug(
                "LTI response failed with error: missing content-item return url"
            )
            raise BadRequest

        lti_parameters = {
            key: value
            for (key, value) in lti_select_form_data.items()
            if "oauth" not in key
        }

        selection = lti_select_form_data.get("selection")

        if not selection:
            logger.debug("LTI response failed with error: no selection")
            raise BadRequest

        selected_url = request.build_absolute_uri(f"/lti/{selection}/")

        content_items = {
            "@context": "http://purl.imsglobal.org/ctx/lti/v1/ContentItem",
            "@graph": [
                {
                    "@type": "ContentItem",
                    "url": selected_url,
                    "frame": [],
                }
            ],
        }

        lti_parameters.update({"content_items": json.dumps(content_items)})

        passport = LTIPassport.objects.get(
            oauth_consumer_key=lti_select_form_data.get("oauth_consumer_key"),
            is_enabled=True,
        )

        client = oauth1.Client(
            client_key=passport.oauth_consumer_key,
            client_secret=passport.shared_secret,
        )

        _uri, headers, _body = client.sign(
            content_item_return_url,
            http_method="POST",
            body=lti_parameters,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        oauth_dict = dict(
            param.strip().replace('"', "").split("=")
            for param in headers["Authorization"].split(",")
        )

        oauth_dict["oauth_signature"] = unquote(oauth_dict["oauth_signature"])
        oauth_dict["oauth_nonce"] = oauth_dict.pop("OAuth oauth_nonce")

        lti_parameters.update(oauth_dict)

        return self.render_to_response(
            {"form_action": content_item_return_url, "form_data": lti_parameters}
        )
