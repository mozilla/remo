from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
# Two line breaks
def permission_check(permissions=[], display_name_field=None):
    """
    Check if a user is logged in and has the required permissions.

    1. If user is not logged in then redirect to 'main', display login
    message

    2. If user logged in and len(permissions) == 0 and
    display_name_field == None then allow access

    3. If user logged in and len(permissions) > 0 and
    display_name_field == None then allow access only if user has all
    permissions

    4. If user logged in and len(permissions) > 0 and
    display_name_field != None then allow access if user has all
    permissions or user.userprofile.display_name == kwargs[display_name_field]

    5. If user logged in and len(permissions) == 0 and
    display_name_field != None then allow access only if
    user.userprofile.display_name == kwargs[display_name_field]

    """
    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if request.user.is_authenticated():
                if (not permissions and not display_name_field) or\
                       (len(permissions) and\
                        request.user.has_perms(permissions)) or\
                       request.user.is_superuser or \
                       (display_name_field and \
                        kwargs[display_name_field] ==\
                        request.user.userprofile.display_name):
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'Permission denied')
                    return redirect('main')
            else:
                messages.warning(request, 'Please login')
                return redirect('main')

        return wraps(view_func)(_view)

    return _dec

