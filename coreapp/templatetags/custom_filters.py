from django import template

register = template.Library()

@register.filter
def unique(queryset, field_name):
    seen = set()
    unique_items = []
    for item in queryset:
        field_value = getattr(item, field_name)
        if field_value not in seen:
            seen.add(field_value)
            unique_items.append(item)
    return unique_items