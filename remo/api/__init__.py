from tastypie.cache import NoCache


class HttpCache(NoCache):
    """Cache class that sets cache-control to response headers."""

    def __init__(self, control={'no_cache': True}, *args, **kwargs):
        super(HttpCache, self).__init__(*args, **kwargs)
        self.control = control

    def cache_control(self):
        return self.control
