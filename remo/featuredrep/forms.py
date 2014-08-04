from django import forms
from django.contrib.auth.models import User

import happyforms

from models import FeaturedRep


class FeaturedRepForm(happyforms.ModelForm):
    """Form to create a new FeaturedRep object."""
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(userprofile__registration_complete=True,
                                     groups__name='Rep'))

    class Meta:
        model = FeaturedRep
        fields = ['users', 'text']
        widgets = {'users': forms.SelectMultiple()}
