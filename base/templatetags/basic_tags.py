from django import template
register = template.Library()

from django.conf import settings


@register.simple_tag
def bool_img(value):
    if bool(value):
        rv = '<img alt="True" src="%sstatic/admin/img/icon-yes.svg">' % settings.STATIC_URL
    else:
        rv = '<img alt="False" src="%sstatic/admin/img/icon-no.svg">' % settings.STATIC_URL
    return rv
