from remo.remozilla.models import Bug, Status


def get_last_updated_date():
    """Get last successful Bugzilla sync datetime."""
    status, created = Status.objects.get_or_create(pk=1)
    return status.last_updated


def set_last_updated_date(date):
    """Set last successful Bugzilla sync datetime."""

    status, c = Status.objects.get_or_create(pk=1)
    status.last_updated = date
    status.save()

    return status.last_updated


def get_bugzilla_url(obj):

    if not isinstance(obj, Bug):
        return ''
    url = 'https://bugzilla.mozilla.org/show_bug.cgi?id='
    return url + '{0}'.format(obj.bug_id)
