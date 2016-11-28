from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect


class RegisterMiddleware(object):
    """Middleware to enforce users to complete registration.

    When a user logins and has the registration_complete field in his
    userprofile set to False the middleware will automatically
    redirect him to edit profile with the appropriate message
    displayed. The only allowed destinations are the edit profile and
    the signout page.

    """

    def process_request(self, request):
        if (request.user.is_authenticated() and not
            request.user.userprofile.registration_complete and not
                request.user.groups.filter(name='Mozillians').exists()):
            allow_urls = [
                reverse('oidc_authentication_init'),
                reverse('oidc_authentication_callback'),
                reverse('oidc_logout'),
                reverse('profiles_edit',
                        kwargs={'display_name':
                                request.user.userprofile.display_name})]

            if (not request.path.startswith(settings.STATIC_URL) and
                    not filter(lambda x: request.path == x, allow_urls)):
                messages.warning(request, 'Please complete your '
                                          'profile before proceeding.')
                return redirect('profiles_edit',
                                request.user.userprofile.display_name)
