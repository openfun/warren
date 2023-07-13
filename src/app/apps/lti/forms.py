"""Warren LTI app forms."""

from django import forms
from django.core import signing
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class BaseLTIUserForm(forms.Form):
    """Warren LTI user form.

    This form is used to validate user initially authenticated via LTI.
    """

    platform = forms.URLField(required=True)
    course = forms.CharField(required=True, max_length=100)
    user = forms.CharField(required=True, max_length=100)
    email = forms.EmailField(required=True)


class SignedLTIUserForm(forms.Form):
    """A LTI user form with a valid signature."""

    signature = forms.CharField(required=True)

    def get_lti_user(self, signature, max_age=3600):
        """Get LTI user corresponding to input signature."""
        return signing.loads(signature, max_age=max_age)

    def clean_signature(self):
        """Validate input signature."""
        signature = self.cleaned_data.get("signature")
        try:
            self.get_lti_user(signature)
        except signing.BadSignature as exc:
            raise ValidationError(_("Request signature is not valid")) from exc
        return signature
