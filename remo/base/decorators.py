from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def permission_check(permissions=[], display_name_field=None):
    """Check if a user is logged in and has the required permissions.

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

    def decorator(func):

        @wraps(func)
        def wrapper(request, *args, **kwargs):

            def _check_if_user_has_permissions():
                if permissions:
                    if request.user.has_perms(permissions):
                        return True
                return False

            def _check_if_user_owns_page():
                if display_name_field:
                    if (kwargs[display_name_field] ==
                        request.user.userprofile.display_name):
                        return True
                return False

            if request.user.is_authenticated():
                if ((not permissions and not display_name_field) or
                    request.user.is_superuser or
                    _check_if_user_owns_page() or
                    _check_if_user_has_permissions()):

                    return func(request, *args, **kwargs)
                else:
                    messages.error(request, 'Permission denied.')
                    return redirect('main')
            else:
                messages.warning(request, 'Please login.')
                return redirect('main')

        return wrapper
    return decorator
