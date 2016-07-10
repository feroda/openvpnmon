from django import template
register = template.Library()

from django.conf import settings

@register.simple_tag
def bool_img(value):
    if bool(value):
        rv = '<img alt="True" src="%simg/admin/icon-yes.gif">' % settings.ADMIN_MEDIA_PREFIX
    else:
        rv = '<img alt="False" src="%simg/admin/icon-no.gif">' % settings.ADMIN_MEDIA_PREFIX
    return rv

