from django import template
register = template.Library()

from django.conf import settings


@register.simple_tag
def bool_img(value):
    if bool(value):
        rv = '<img alt="True" src="%sadmin/img/icon-yes.svg">' % settings.STATIC_URL
    else:
        rv = '<img alt="False" src="%sadmin/img/icon-no.svg">' % settings.STATIC_URL
    return rv
@register.simple_tag
def static_url():
    return settings.STATIC_URL
