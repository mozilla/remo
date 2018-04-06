from django.conf import settings
from django.contrib.auth.models import Group, User

from mozilla_django_oidc.auth import OIDCAuthenticationBackend, default_username_algo

from remo.base.mozillians import BadStatusCode, MozilliansClient, ResourceDoesNotExist


USERNAME_ALGO = getattr(settings, 'OIDC_USERNAME_ALGO', default_username_algo)


class RemoAuthenticationBackend(OIDCAuthenticationBackend):
    """Authentication Backend for the ReMo portal."""

    def __init__(self, *args, **kwargs):
        """Initialize mozillians.org API v2 client."""
        self.mozillian_user = None
        self.mozillians_client = MozilliansClient(settings.MOZILLIANS_API_URL,
                                                  settings.MOZILLIANS_API_KEY)
        super(RemoAuthenticationBackend, self).__init__(*args, **kwargs)

    def create_user(self, claims):
        """ Override create_user method to anonymize user data
        based on privacy settings in mozillians.org.
        """
        email = claims.get('email')
        try:
            self.mozillian_user = self.mozillians_client.lookup_user({'email': email})
        except (BadStatusCode, ResourceDoesNotExist):
            return None

        # Add vouched mozillians to our db please.
        if self.mozillian_user and self.mozillian_user['is_vouched']:
            user = User.objects.create_user(username=USERNAME_ALGO(email),
                                            email=email)
            # Due to privacy settings, this might be missing
            if self.mozillian_user['full_name']['privacy'] != 'Public':
                full_name = 'Anonymous Mozillian'
            else:
                full_name = self.mozillian_user['full_name']['value']
                user.userprofile.mozillian_username = self.mozillian_user['username']
                user.userprofile.save()

            first_name, last_name = (full_name.split(' ', 1) if ' ' in full_name
                                     else ('', full_name))
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            user.groups.add(Group.objects.get(name='Mozillians'))
            return user

    def authenticate(self, **kwargs):
        """ Override authenticate method in order to combine with other backends.
        It was fixed with PR #87 and released in version 0.2.0
        """
        # TODO: remove this override whenever upgrade `mozilla-django-oidc` to version 0.2.0
        if not kwargs.get('request'):
            return None

        return super(RemoAuthenticationBackend, self).authenticate(**kwargs)
