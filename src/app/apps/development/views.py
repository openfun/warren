"""Views for the development app."""

from logging import getLogger
from urllib.parse import unquote, urlparse

from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from lti_toolbox.models import LTIConsumer, LTIPassport
from oauthlib import oauth1

from warren.settings import Development

logger = getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(xframe_options_exempt, name="dispatch")
class DevelopmentLTIRequestView(TemplateView):
    """A development view for LTI requests with iframe POST / plain POST helpers.

    Not available outside of DEBUG = true environments.
    """

    template_name = "development/lti_request.html"

    def get_context_data(self, **kwargs):
        """Pre-populate fields in the LTI request form.

        Parameters
        ----------
        kwargs : dictionary
            keyword extra arguments

        Returns:
        -------
        dictionary
            context for template rendering.
        """
        return {
            "lti_parameters": Development.LTI_PARAMETERS.copy(),
            "lti_routes": Development.LTI_ROUTES,
        }

    def post(self, request, *args, **kwargs):
        """Respond to POST request on the refresh button.

        Context populated with POST request.

        Parameters
        ----------
        request : Request
            passed by Django
        args : list
            positional extra arguments
        kwargs : dictionary
            keyword extra arguments

        -------
        HTML
            generated from applying the data to the template

        """
        request_params = request.POST.dict()
        route = request_params.get("route")
        excluded_params = ["route", "refresh_signature"]
        lti_parameters = {
            key: value
            for key, value in request_params.items()
            if key not in excluded_params and "oauth" not in key
        }

        # use the HTTP_REFERER like to be consistent with the LTI passport
        launch_url = (
            urlparse(self.request.build_absolute_uri())
            ._replace(
                path=reverse(
                    "lti:lti-request-view",
                    kwargs={"selection": route},
                )
            )
            .geturl()
        )
        try:
            lti_consumer = LTIConsumer.objects.get(url=launch_url)
        except LTIConsumer.DoesNotExist:
            lti_consumer, _ = LTIConsumer.objects.get_or_create(
                slug=f"localhost-{route}",
                title=f"localhost test - {route}",
                url=launch_url,
            )

        passport, _ = LTIPassport.objects.get_or_create(
            consumer=lti_consumer, title="Development passport"
        )

        oauth_client = oauth1.Client(
            client_key=passport.oauth_consumer_key,
            client_secret=passport.shared_secret,
        )
        # Compute Authorization header which looks like:
        # Authorization: OAuth oauth_nonce="80966668944732164491378916897",
        # oauth_timestamp="1378916897", oauth_version="1.0",
        # oauth_signature_method="HMAC-SHA1", oauth_consumer_key="",
        # oauth_signature="frVp4JuvT1mVXlxktiAUjQ7%2F1cw%3D"
        _uri, headers, _body = oauth_client.sign(
            launch_url,
            http_method="POST",
            body=lti_parameters,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Parse headers to pass to template as part of context:
        oauth_dict = dict(
            param.strip().replace('"', "").split("=")
            for param in headers["Authorization"].split(",")
        )

        signature = oauth_dict["oauth_signature"]
        oauth_dict["oauth_signature"] = unquote(signature)
        oauth_dict["oauth_nonce"] = oauth_dict.pop("OAuth oauth_nonce")
        lti_parameters.update({"oauth_dict": oauth_dict})

        return self.render_to_response(
            {
                "lti_routes": Development.LTI_ROUTES,
                "selected_route": route,
                "lti_parameters": lti_parameters,
                "launch_url": launch_url,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(xframe_options_exempt, name="dispatch")
class DevelopmentLTISelectView(TemplateView):
    """A development view for LTI select with iframe POST / plain POST helpers.

    Not available outside of DEBUG = true environments.
    """

    template_name = "development/lti_select.html"

    def get_context_data(self, **kwargs):
        """Pre-populate fields in the LTI select form.

        Parameters
        ----------
        kwargs : dictionary
            keyword extra arguments

        Returns:
        -------
        dictionary
            context for template rendering.
        """
        return {
            "lti_message_type": "ContentItemSelectionRequest",
            "lti_version": "LTI-1p0",
            "lis_person_contact_email_primary": "admin@example.com",
            "user_id": "1234",
            "roles": "instructor",
            "context_id": "2",
            "context_title": "Mathematics 101",
            "content_item_return_url": self.request.build_absolute_uri(
                reverse("development:lti-select-view")
            ),
            "tool_consumer_instance_name": "FUN",
            "tool_consumer_info_product_family_code": "moodle",
            "accept_presentation_document_targets": "frame,iframe,window",
            "accept_media_types": "application/vnd.ims.lti.v1.ltilink",
        }

    def post(self, request, *args, **kwargs):
        """Respond to POST request on the refresh button.

        Context populated with POST request.

        Parameters
        ----------
        request : Request
            passed by Django
        args : list
            positional extra arguments
        kwargs : dictionary
            keyword extra arguments

        -------
        HTML
            generated from applying the data to the template

        """
        request_params = request.POST.dict()
        excluded_params = ["refresh_signature"]
        lti_parameters = {
            key: value
            for key, value in request_params.items()
            if key not in excluded_params and "oauth" not in key
        }

        # use the HTTP_REFERER like to be consistent with the LTI passport
        select_url = (
            urlparse(self.request.build_absolute_uri())
            ._replace(path=reverse("lti:lti-select-view"))
            .geturl()
        )
        try:
            lti_consumer = LTIConsumer.objects.get(url=select_url)
        except LTIConsumer.DoesNotExist:
            lti_consumer, _ = LTIConsumer.objects.get_or_create(
                slug="localhost",
                title="localhost test",
                url=select_url,
            )

        passport, _ = LTIPassport.objects.get_or_create(
            consumer=lti_consumer, title="Development passport"
        )

        oauth_client = oauth1.Client(
            client_key=passport.oauth_consumer_key,
            client_secret=passport.shared_secret,
        )
        # Compute Authorization header which looks like:
        # Authorization: OAuth oauth_nonce="80966668944732164491378916897",
        # oauth_timestamp="1378916897", oauth_version="1.0",
        # oauth_signature_method="HMAC-SHA1", oauth_consumer_key="",
        # oauth_signature="frVp4JuvT1mVXlxktiAUjQ7%2F1cw%3D"
        _uri, headers, _body = oauth_client.sign(
            select_url,
            http_method="POST",
            body=lti_parameters,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Parse headers to pass to template as part of context:
        oauth_dict = dict(
            param.strip().replace('"', "").split("=")
            for param in headers["Authorization"].split(",")
        )

        signature = oauth_dict["oauth_signature"]
        oauth_dict["oauth_signature"] = unquote(signature)
        oauth_dict["oauth_nonce"] = oauth_dict.pop("OAuth oauth_nonce")
        lti_parameters.update({"oauth_dict": oauth_dict})

        return self.render_to_response(lti_parameters)
