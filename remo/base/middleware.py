from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect


class RegisterMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated() and not\
               request.user.userprofile.registration_complete:

            if not request.path.startswith('/media') and\
                    request.path != reverse('logout') and\
                     request.path != reverse('profiles_edit',
                                             kwargs={'display_name':
                                                     request.user.userprofile.display_name}
                                             ):

                messages.warning(request,
                                 'Please complete your profile before proceeding')
                return redirect('profiles_edit', request.user.userprofile.display_name)


