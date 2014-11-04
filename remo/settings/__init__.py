import os

from .base import *  # noqa


if os.environ.get('VCAP_APPLICATION'):
    # This is a stackato env, load stackato settings.
    try:
        from .localstackato import *  # noqa
    except ImportError as exc:
        raise Exception('Error importing stackato local settings: %s' % exc)
elif os.environ.get('TRAVIS'):
    try:
        from .localtravis import *  # noqa
    except ImportError as exc:
        raise Exception('Error importing travis local settings: %s' % exc)
else:
    try:
        from .local import *  # noqa
    except ImportError as exc:
        exc.args = tuple(['%s (did you rename settings/local.py-dist?)' %
                          exc.args[0]])
        raise exc
