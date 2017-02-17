import os

if os.environ.get('MESOS_CLUSTER'):
    from .base_env_vars import *  # noqa
else:
    from .base import *  # noqa

    if os.environ.get('TRAVIS'):
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
