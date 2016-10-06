from rest_framework.viewsets import ReadOnlyModelViewSet


class BaseReadOnlyModelViewset(ReadOnlyModelViewSet):
    """Amends API response to add CORS headers."""
    def dispatch(self, request, *args, **kwargs):
        response = super(BaseReadOnlyModelViewset, self).dispatch(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'
        return response
