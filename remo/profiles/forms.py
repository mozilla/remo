import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from happyforms import forms

from remo.profiles.models import UserProfile


class InviteUserForm(forms.Form):
    """Form to invite a new user."""

    def _validate_unique_email(data, **kwargs):
        # Django does not require unique emails but we do.
        if User.objects.filter(email=data).exists():
            raise ValidationError('User already exists.')

        return data

    email = forms.EmailField(label='Email',
                             validators=[_validate_unique_email])


class ChangeUserForm(forms.ModelForm):
    """Form to change user details."""
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def _clean_names(self, data):
        """Ensure that data is valid.

        Variable data can contain only latin letters (both capital and
        lower case), spaces and the character '.
        """
        if not re.match(r'(^[A-Za-z\' ]+$)', data):
            raise ValidationError('Please use only latin characters.')

        return data

    def clean_first_name(self):
        """Ensure that first_name is valid."""

        data = self.cleaned_data['first_name']
        return self._clean_names(data)

    def clean_last_name(self):
        """Ensure that last_name is valid."""

        data = self.cleaned_data['last_name']
        return self._clean_names(data)


class ChangeProfileForm(forms.ModelForm):
    """Form to change userprofile details."""

    class Meta:
        model = UserProfile
        fields = ('local_name', 'birth_date',
                  'city', 'region', 'country',
                  'lon', 'lat', 'display_name',
                  'private_email', 'mozillians_profile_url',
                  'twitter_account', 'jabber_id', 'irc_name',
                  'irc_channels', 'facebook_url', 'linkedin_url',
                  'diaspora_url', 'personal_website_url', 'personal_blog_feed',
                  'bio', 'gender', 'mentor', 'wiki_profile_url')

    def clean_twitter_account(self):
        """Make sure that twitter_account does not start with a '@'."""
        twitter_account = self.cleaned_data['twitter_account']
        return twitter_account.strip('@')
