from tastypie.authorization import ReadOnlyAuthorization


class WebAuthorization(ReadOnlyAuthorization):
    """Authorize user as logged in current session or external."""

    def is_authorized(self, request, object=None):
        """Enable restricted data when user is authenticated."""

        if request.user.is_authenticated():
            data = request.GET.copy()
            data['restricted'] = 'True'
            request.GET = data

        return True
