from django import template

register = template.Library()


@register.filter(name='is_instance')
def is_instance(instance, cls):
    return isinstance(instance, cls)


@register.filter(name='to_str')
def to_str(value):
    if value is None:
        return ''
    return str(value)
