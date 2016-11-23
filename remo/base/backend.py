from django.conf import settings
from django.contrib.auth.models import Group, User

from mozilla_django_oidc.auth import OIDCAuthenticationBackend, default_username_algo

from remo.base.mozillians import BadStatusCodeError, is_vouched


USERNAME_ALGO = getattr(settings, 'OIDC_USERNAME_ALGO', default_username_algo)


class RemoAuthenticationBackend(OIDCAuthenticationBackend):
    """Authentication Backend for the ReMo portal."""

    def create_user(self, claims):
        """ Override create_user method to anonymize user data
        based on privacy settings in mozillians.org.
        """
        email = claims.get('email')
        try:
            data = is_vouched(email)
        except BadStatusCodeError:
            data = None

        # Add vouched mozillians to our db please.
        if data and data['is_vouched']:
            user = User.objects.create_user(username=USERNAME_ALGO(email),
                                            email=email)
            # Due to privacy settings, this might be missing
            if 'full_name' not in data:
                data['full_name'] = 'Anonymous Mozillian'
            else:
                user.userprofile.mozillian_username = data['username']
                user.userprofile.save()

            first_name, last_name = (data['full_name'].split(' ', 1)
                                     if ' ' in data['full_name']
                                     else ('', data['full_name']))
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            user.groups.add(Group.objects.get(name='Mozillians'))
            return user
