from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def bool_img(value):
    if bool(value):
        rv = '<img alt="True" src="/media/img/admin/icon-yes.gif">'
    else:
        rv = '<img alt="False" src="/media/img/admin/icon-no.gif">'
    return rv


@register.simple_tag
def static_url():
    return settings.STATIC_URL
