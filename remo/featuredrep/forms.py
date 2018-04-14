from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.timezone import now
import datetime

import happyforms

from models import FeaturedRep


class FeaturedRepForm(happyforms.ModelForm):
    """Form to create a new FeaturedRep object."""
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(
            userprofile__registration_complete=True,
            groups__name='Rep').order_by('first_name'))

    def clean_created_on(self):
        if 'created_on' in self.cleaned_data and self.cleaned_data['created_on'] > now() + datetime.timedelta(days=30):
            raise ValidationError('The date cannot be over 30 days in the future.')

        return self.cleaned_data['created_on']

    class Meta:
        model = FeaturedRep
        fields = ['users', 'text', 'created_on']
        widgets = {'users': forms.SelectMultiple()}
