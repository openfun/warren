"""Views for the development app."""

import uuid
from logging import getLogger
from urllib.parse import unquote, urlparse

from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from lti_toolbox.models import LTIConsumer, LTIPassport
from oauthlib import oauth1

logger = getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(xframe_options_exempt, name="dispatch")
class DevelopmentLTIView(TemplateView):
    """A development view with iframe POST / plain POST helpers.

    Not available outside of DEBUG = true environments.
    """

    template_name = "development/lti_development.html"

    def get_context_data(self, **kwargs):
        """Generate a UUID to pre-populate the `uuid` fields in the LTI request form.

        Parameters
        ----------
        kwargs : dictionary
            keyword extra arguments

        Returns:
        -------
        dictionary
            context for template rendering.
        """
        lti_parameters = {
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": str(uuid.uuid4()),
            "lis_person_contact_email_primary": "johndoe@example.com",
            "lis_person_sourcedid": "johndoe",
            "context_id": "course-v1:openfun+mathematics101+session01",
            "context_title": "Mathematics 101",
            "roles": "student",
            "launch_presentation_locale": "fr",
        }

        # use the HTTP_REFERER like to be consistent with the LTI passport
        request_url = (
            urlparse(self.request.build_absolute_uri())
            ._replace(path=reverse("lti:lti-request-view"))
            .geturl()
        )
        try:
            lti_consumer = LTIConsumer.objects.get(url=request_url)
        except LTIConsumer.DoesNotExist:
            lti_consumer, _ = LTIConsumer.objects.get_or_create(
                slug="localhost",
                title="localhost test",
                url=request_url,
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
            request_url,
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

        return lti_parameters
