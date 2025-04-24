from django import template

register = template.Library()

@register.filter
def times(number):
    return range(number)

@register.filter
def index(sequence, position):
    return sequence[position]