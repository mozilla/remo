import re

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from remo.profiles.models import UserProfile

class InviteUserForm(forms.Form):
    email = forms.EmailField(label='Email')


class ChangeUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


    # I'm curious why the first name and last name have to be latin?
    # Do you not want users to have numbers in their name? Could you just
    # match \w?
    def clean_first_name(self):
        # Missing comment
        data = self.cleaned_data['first_name']
        print data
        if not re.match(r'(^[A-Za-z\' ]+$)', data):
            raise ValidationError("Please use only latin characters.")

        return data

    def clean_last_name(self):
        # Missing comment
        data = self.cleaned_data['last_name']
        if not re.match(r'(^[A-Za-z\' ]+)$', data):
            raise ValidationError("Please use only latin characters.")

        return data


class ChangeProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('local_name', 'birth_date',
                  'city', 'region', 'country',
                  'lon', 'lat', 'display_name',
                  'private_email', 'mozillians_profile_url',
                  'twitter_account', 'jabber_id', 'irc_name',
                  'irc_channels', 'facebook_url', 'diaspora_url',
                  'personal_website_url', 'personal_blog_feed',
                  'bio', 'gender', 'mentor')


    def clean_twitter_account(self):
        twitter_account = self.cleaned_data['twitter_account']
        return twitter_account.strip('@')
