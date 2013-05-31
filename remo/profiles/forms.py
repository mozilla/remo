import happyforms
import re
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms.extras.widgets import SelectDateWidget

from django_browserid.auth import default_username_algo
from product_details import product_details

from remo.profiles.models import UserProfile

USERNAME_ALGO = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)


class InviteUserForm(happyforms.Form):
    """Form to invite a new user."""

    def _validate_unique_email(data, **kwargs):
        # Django does not require unique emails but we do.
        if User.objects.filter(email=data).exists():
            user = User.objects.filter(email=data)
            if user and user[0].groups.filter(name='Mozillians').exists():
                user[0].delete()
            else:
                raise ValidationError('User already exists.')

        return data

    email = forms.EmailField(label='Email',
                             validators=[_validate_unique_email])


class ChangeUserForm(happyforms.ModelForm):
    """Form to change user details."""
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def _clean_names(self, data):
        """Ensure that data is valid.

        Variable data can contain only Latin letters (both capital and
        lower case), spaces and the character '.
        """
        if not re.match(r'(^[A-Za-z\' ]+$)', data):
            raise ValidationError('Please use only Latin characters.')

        return data

    def clean_first_name(self):
        """Ensure that first_name is valid."""

        data = self.cleaned_data['first_name']
        return self._clean_names(data)

    def clean_last_name(self):
        """Ensure that last_name is valid."""

        data = self.cleaned_data['last_name']
        return self._clean_names(data)

    def save(self):
        """Override save method to update user's
        username hash on the database.

        """
        self.instance.username = USERNAME_ALGO(self.instance.email)
        super(ChangeUserForm, self).save()


class ChangeProfileForm(happyforms.ModelForm):
    """Form to change userprofile details."""
    gender = forms.ChoiceField(required=False, choices=((None, "Gender"),
                                                        (True, "Female"),
                                                        (False, "Male")))
    mentor = forms.ChoiceField(choices=[])
    country = forms.ChoiceField(
        choices=[],
        error_messages={'required': 'Please select one option from the list.'})

    def __init__(self, *args, **kwargs):
        """Initialize form.

        Dynamically set choices for mentor and country fields.
        """
        super(ChangeProfileForm, self).__init__(*args, **kwargs)
        mentor_choices = ([(None, "Choose Mentor")] +
                          [(u.id, u.get_full_name()) for u in
                           User.objects.filter(
                               userprofile__registration_complete=True,
                               groups__name='Mentor')])
        self.fields['mentor'].choices = mentor_choices

        countries = product_details.get_regions('en').values()
        countries.sort()
        country_choices = ([('', "Country")] +
                           [(country, country) for country in countries])
        self.fields['country'].choices = country_choices

    def clean_twitter_account(self):
        """Make sure that twitter_account does not start with a '@'."""
        twitter_account = self.cleaned_data['twitter_account']
        return twitter_account.strip('@')

    def clean_mentor(self):
        """Convert mentor field from number to User."""
        value = self.cleaned_data['mentor']
        if value == u'None':
            raise ValidationError('Please select a mentor.')

        value = User.objects.get(pk=value)
        return value

    class Meta:
        model = UserProfile
        fields = ('local_name', 'birth_date',
                  'city', 'region', 'country',
                  'lon', 'lat', 'display_name',
                  'private_email', 'mozillians_profile_url',
                  'twitter_account', 'jabber_id', 'irc_name',
                  'irc_channels', 'facebook_url', 'linkedin_url',
                  'diaspora_url', 'personal_website_url', 'personal_blog_feed',
                  'bio', 'gender', 'mentor', 'wiki_profile_url',
                  'functional_areas')


class ChangeDateJoinedForm(happyforms.ModelForm):
    """Form to change userprofile date_joined_program field."""
    date_joined_program = forms.DateField(
        required=False,
        widget=SelectDateWidget(years=range(2011, datetime.today().year + 1),
                                required=False))

    class Meta:
        model = UserProfile
        fields = ['date_joined_program']
