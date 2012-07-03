from django.conf import settings
from django.core.urlresolvers import reverse
from jingo import register


@register.filter
def get_event_converted_visitor_callback_url(obj):
    """Return event converted visitor callback url."""
    return settings.SITE_URL + reverse('events_count_converted_visitors',
                                       kwargs={'slug': obj.slug})
