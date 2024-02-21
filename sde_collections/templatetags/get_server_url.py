from django import template

register = template.Library()


@register.simple_tag
def get_server_url(collection, server_name):
    return collection.get_server_url(server_name)
