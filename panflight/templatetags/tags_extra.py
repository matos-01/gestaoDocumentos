import datetime
import os

from django.template import Library

register = Library()

@register.filter(expects_localtime=True)
def parse_date(value):
    if type(value) is not str:
        return datetime.datetime.strftime(value, "%d/%m/%Y")
    else:
        return value

@register.simple_tag
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def filename(value):
    return os.path.basename(value.name)

@register.filter
def in_user_group(user, group):
    return group in user.groups.all().values_list('name', flat=True)
