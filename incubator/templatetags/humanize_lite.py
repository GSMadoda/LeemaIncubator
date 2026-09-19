from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def rands(value):
    """Format as whole Rand with South African space thousands separators: 1250000 -> '1 250 000'."""
    try:
        n = int(Decimal(value).quantize(Decimal("1")))
    except (InvalidOperation, TypeError, ValueError):
        return value
    return f"{n:,}".replace(",", "\u00a0")


@register.filter
def get(mapping, key):
    return mapping.get(key, key)
