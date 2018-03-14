from django import forms
from django.contrib.auth.models import User

import happyforms

from models import FeaturedRep


class FeaturedRepForm(happyforms.ModelForm):
    """Form to create a new FeaturedRep object."""
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(
            userprofile__registration_complete=True,
            groups__name='Rep').order_by('first_name'))

    class Meta:
        model = FeaturedRep
        fields = ['users', 'text', 'created_on']
        widgets = {'users': forms.SelectMultiple()}
