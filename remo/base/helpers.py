from django.contrib.markup.templatetags import markup
from jingo import register


@register.filter
def restructuredtext(text):
    return markup.restructuredtext(text)
