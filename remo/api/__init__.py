from tastypie import http
from tastypie.cache import NoCache
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.throttle import CacheThrottle


default_app_config = 'remo.api.apps.ApiConfig'


class HttpCache(NoCache):
    """Cache class that sets cache-control to response headers."""

    def __init__(self, control={'no_cache': True}, *args, **kwargs):
        super(HttpCache, self).__init__(*args, **kwargs)
        self.control = control

    def cache_control(self):
        return self.control


class RemoThrottleMixin(object):
    """API mixin to check for jsonp requests."""
    def throttle_check(self, request):
        # Check for JSONP request
        identifier = self._meta.authentication.get_identifier(request)
        kwargs = {
            'is_jsonp': self.determine_format(request) == 'text/javascript'
        }

        if self._meta.throttle.should_be_throttled(identifier, **kwargs):
            # Throttle limit exceeded.
            msg = 'Too Many Requests'
            response = http.HttpTooManyRequests(content=msg)
            raise ImmediateHttpResponse(response=response)


class RemoAPIThrottle(CacheThrottle):
    """Throttle class for ReMo API."""
    def should_be_throttled(self, req_id, **kwargs):
        is_jsonp = kwargs.pop('is_jsonp', False)
        is_throttled = (super(RemoAPIThrottle, self)
                        .should_be_throttled(req_id, **kwargs))

        if is_jsonp and is_throttled:
            return True
        return False
