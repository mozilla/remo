from django.conf import settings
from django.utils import translation


def globals(request):
    return {'request': request,
            'settings': settings}
