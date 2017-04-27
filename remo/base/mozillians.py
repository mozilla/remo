import requests

try:
    from urllib.parse import urljoin, urlparse
except ImportError:
    # Python 2.7 compatibility
    from urlparse import urljoin, urlparse


class BadStatusCode(Exception):
    """Bad status code exception."""
    pass


class ResourceDoesNotExist(Exception):
    """Resource does not exist exception."""
    pass


class MultipleResourcesReturned(Exception):
    """Multiple resources returned exception."""
    pass


class MozilliansClient(object):
    """Client to connect to mozillians.org v2 API."""

    def __init__(self, api_base_url, api_key):
        """API v2 client."""

        # Validate api_base_url
        o = urlparse(api_base_url)
        if all([o.scheme in ['http', 'https'], o.netloc, o.path.startswith('/api/v2')]):
            self.base_url = api_base_url
        else:
            raise Exception('Invalid API base URL.')

        self.key = api_key
        self.headers = {'X-API-KEY': self.key}

    def get(self, url, params=None):
        """GET url, checks status code and return json response."""
        response = requests.get(url, headers=self.headers, params=params)

        if not response.status_code == 200:
            raise BadStatusCode('{0} on: {1}'.format(response.status_code, url))

        return response.json()

    def _get_resource_url(self, resource):
        """Build Mozillians.org API resource url."""
        return urljoin(self.base_url, resource)

    def get_users(self, params=None):
        """GET Mozillians.org users."""
        url = self._get_resource_url('users')
        return self.get(url, params=params)

    def get_groups(self, params=None):
        """GET Mozillians.org groups"""
        url = self._get_resource_url('groups')
        return self.get(url, params=params)

    def get_skills(self, params=None):
        """GET Mozillians.org skills."""
        url = self._get_resource_url('skills')
        return self.get(url, params=params)

    def get_user(self, user_id):
        """GET Mozillians.org user by id."""
        url = self._get_resource_url('users/{0}/'.format(user_id))
        return self.get(url)

    def get_group(self, group_id):
        """GET Mozillians.org group by id."""
        url = self._get_resource_url('groups/{0}/'.format(group_id))
        return self.get(url)

    def get_skill(self, skill_id):
        """GET Mozillians.org skill by id."""
        url = self._get_resource_url('skills/{0}/'.format(skill_id))
        return self.get(url)

    def _lookup_resource(self, resource, params, detailed):
        url = self._get_resource_url(resource)
        query = self.get(url, params)

        # Check if only single resource gets returned
        if query['count'] == 0:
            raise ResourceDoesNotExist()
        if query['count'] > 1:
            raise MultipleResourcesReturned()

        if detailed:
            return self.get(query['results'][0]['_url'])
        return query['results'][0]

    def lookup_user(self, params, detailed=True):
        """Lookup Mozillians.org based on email."""
        return self._lookup_resource('users', params=params, detailed=detailed)

    def lookup_group(self, params, detailed=True):
        """Lookup Mozillians.org group based on params."""
        return self._lookup_resource('groups', params=params, detailed=detailed)

    def lookup_skill(self, params, detailed=True):
        """Lookup Mozillians.org skills based on params."""
        return self._lookup_resource('groups', params=params, detailed=detailed)

    def is_vouched(self, email):
        """Check users vouched status based on email."""
        user = self.lookup_user({'email': email}, detailed=False)
        return (user, user['is_vouched'])
