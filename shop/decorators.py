# shop/decorators.py (yangi fayl yaratish)
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Shop, Sale


def owner_required(view_func):
    """Faqat do'kon egasi (glavniy admin) uchun decorator"""

    def _wrapped_view(request, *args, **kwargs):
        shop_id = kwargs.get("shop_id")
        sale_id = kwargs.get("sale_id")

        if shop_id:
            shop = get_object_or_404(Shop, id=shop_id)
            if shop.owner != request.user:
                raise PermissionDenied("Faqat do'kon egasi bu amalni bajarishi mumkin!")

        if sale_id:
            sale = get_object_or_404(Sale, id=sale_id)
            if sale.shop.owner != request.user:
                raise PermissionDenied("Faqat do'kon egasi bu amalni bajarishi mumkin!")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def admin_required(view_func):
    """Admin yoki owner uchun decorator"""

    def _wrapped_view(request, *args, **kwargs):
        shop_id = kwargs.get("shop_id")

        if shop_id:
            shop = get_object_or_404(Shop, id=shop_id)
            is_owner = shop.owner == request.user
            is_admin = shop.staff.filter(user=request.user, role="admin").exists()

            if not (is_owner or is_admin):
                raise PermissionDenied("Bu amalni bajarish uchun admin huquqi kerak!")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def cashier_or_above_required(view_func):
    """Kassir, admin yoki owner uchun decorator"""

    def _wrapped_view(request, *args, **kwargs):
        shop_id = kwargs.get("shop_id")

        if shop_id:
            shop = get_object_or_404(Shop, id=shop_id)
            is_owner = shop.owner == request.user
            is_staff = shop.staff.filter(user=request.user).exists()

            if not (is_owner or is_staff):
                raise PermissionDenied("Bu amalni bajarish uchun xodim huquqi kerak!")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
