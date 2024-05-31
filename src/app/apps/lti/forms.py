"""Warren LTI app forms."""

from django import forms


class BaseLTIContextForm(forms.Form):
    """Warren LTI context form.

    This form is used to validate context from LTI request.
    """

    consumer_site = forms.URLField(required=True)
    course_id = forms.CharField(required=True)


class BaseLTIUserForm(forms.Form):
    """Warren LTI user form.

    This form is used to validate user initially authenticated via LTI.
    """

    id = forms.CharField(required=True, max_length=100)
    email = forms.EmailField(required=True)
