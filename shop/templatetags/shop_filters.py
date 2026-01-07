# shop/templatetags/shop_filters.py (yangi fayl)
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def format_price(value):
    """Narxni chiroyli formatlash: 6 000 yoki 6.000"""
    if value is None:
        return "0"

    try:
        # Agar string bo'lsa, float ga o'tkazish
        if isinstance(value, str):
            value = float(value)

        # Butun son bo'lsa
        if isinstance(value, int) or value.is_integer():
            # 6 000 format
            formatted = "{:,}".format(int(value)).replace(",", " ")
            return mark_safe(f'<span class="price-amount">{formatted}</span>')
        else:
            # 6.000 format (o'nlik kasrlar uchun)
            formatted = "{:,.2f}".format(value).replace(",", " ")
            # Kasrni to'g'ri formatlash
            formatted = (
                formatted.rstrip("0").rstrip(".") if "." in formatted else formatted
            )
            return mark_safe(f'<span class="price-amount">{formatted}</span>')

    except (ValueError, TypeError, AttributeError):
        return value


@register.filter
def format_price_with_currency(value, currency="so'm"):
    """Narxni valyuta bilan formatlash: 6 000 so'm"""
    formatted = format_price(value)
    if formatted and formatted != value:  # Agar formatlash muvaffaqiyatli bo'lsa
        return mark_safe(f'{formatted} <span class="price-currency">{currency}</span>')
    return f"{value} {currency}"


@register.filter
def format_quantity(value):
    """Miqdorni formatlash: 1 000 dona"""
    if value is None:
        return "0"

    try:
        value = int(value)
        formatted = "{:,}".format(value).replace(",", " ")
        return mark_safe(f'<span class="quantity-amount">{formatted}</span> dona')
    except (ValueError, TypeError):
        return f"{value} dona"

    # shop/templatetags/shop_filters.py - OXIRIGA QO'SHING


@register.filter
def format_quantity_with_unit(product):
    """Mahsulot miqdorini birligi bilan formatlash: 5 kg, 10 dona"""
    if hasattr(product, "get_display_quantity"):
        return product.get_display_quantity()

    # Agar product object bo'lmasa, oddiy formatlash
    try:
        if hasattr(product, "quantity") and hasattr(product, "unit"):
            quantity = int(product.quantity) if product.quantity else 0
            unit = product.unit if product.unit else "dona"
            formatted = "{:,}".format(quantity).replace(",", " ")
            return mark_safe(
                f'<span class="quantity-amount">{formatted}</span> <span class="badge-unit">{unit}</span>'
            )
    except (ValueError, TypeError, AttributeError):
        pass

    return "0 dona"


@register.filter
def format_price_input(value):
    """Input field uchun narx formatlash: 17 000"""
    if value is None or value == "":
        return ""

    try:
        # String bo'lsa, float ga o'tkazish
        if isinstance(value, str):
            # Bo'shliqlar va vergullarni olib tashlash
            value = value.replace(" ", "").replace(",", "")
            try:
                value = float(value)
            except ValueError:
                # Agar float ga o'tkazib bo'lmasa, int ga urinib ko'rish
                value = int(value)

        # Butun son bo'lsa
        if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
            # 17 000 format
            formatted = "{:,}".format(int(value)).replace(",", " ")
            return formatted
        else:
            # Kasrli sonlar uchun
            formatted = "{:,.2f}".format(value).replace(",", " ")
            # Keraksiz nollarni olib tashlash
            formatted = (
                formatted.rstrip("0").rstrip(".") if "." in formatted else formatted
            )
            return formatted

    except (ValueError, TypeError, AttributeError):
        # Xato bo'lsa, original qiymatni qaytarish
        return str(value)
