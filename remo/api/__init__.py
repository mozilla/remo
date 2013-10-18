# Implement HTTP Caching
# code from http://django-tastypie.readthedocs.org/en/latest/caching.html
from django.utils.cache import patch_cache_control


class ClientCachedResource(object):
    """
    Mixin class which sets Cache-Control headers on API responses
    using a ``cache_control`` dictionary from the resource's Meta
    class.

    """

    def create_response(self, request, data, **response_kwargs):
        response = (super(ClientCachedResource, self)
                    .create_response(request, data, **response_kwargs))

        if ((request.method == "GET" and response.status_code == 200
             and hasattr(self.Meta, "cache_control"))):

            cache_control = self.Meta.cache_control.copy()
            patch_cache_control(response, **cache_control)

        return response
