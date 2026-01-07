# shop/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .decorators import owner_required
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse
from decimal import Decimal
from .models import (
    Shop,
    ShopApplication,
    ShopCategory,
    ShopStaff,
    Product,
    ProductIncome,
    Sale,
)
from .forms import (
    RegisterForm,
    LoginForm,
    ShopApplicationForm,
    ShopForm,
    ProductForm,
    StaffForm,
    SaleForm,
)
from .telegram_utils import send_application_to_admin


def register_view(request):
    """Ro'yxatdan o'tish"""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(
                request,
                "Muvaffaqiyatli ro'yxatdan o'tdingiz! Endi tizimga kirishingiz mumkin.",
            )
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "shop/register.html", {"form": form})


def login_view(request):
    """Tizimga kirish"""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Xush kelibsiz, {user.username}!")
                return redirect("home")
            else:
                messages.error(request, "Login yoki parol noto'g'ri!")
    else:
        form = LoginForm()

    return render(request, "shop/login.html", {"form": form})


@login_required
def logout_view(request):
    """Tizimdan chiqish"""
    logout(request)
    messages.info(request, "Tizimdan muvaffaqiyatli chiqdingiz.")
    return redirect("login")


# shop/views.py ga yangi funksiya qo'shing
@login_required
def restore_sale_view(request, sale_id):
    """Bekor qilingan sotuvni qayta tiklash (faqat glavniy admin)"""
    sale = get_object_or_404(Sale, id=sale_id)
    shop = sale.shop

    # Faqat glavniy admin (owner) qilishi mumkin
    if shop.owner != request.user:
        messages.error(
            request, "Faqat do'kon egasi (glavniy admin) sotuvni qayta tiklay oladi!"
        )
        return redirect("sales_history", shop_id=shop.id)

    if not sale.is_cancelled:
        messages.warning(request, "Bu sotuv allaqachon bekor qilinmagan!")
        return redirect("sales_history", shop_id=shop.id)

    if request.method == "POST":
        # Formadan sabab olish
        restoration_reason = request.POST.get("restoration_reason", "")

        # Sotuvni qayta tiklash
        sale.is_cancelled = False
        sale.restored_by = request.user
        sale.restoration_reason = restoration_reason
        from django.utils import timezone

        sale.restored_at = timezone.now()
        sale.save()

        # Mahsulot miqdorini kamaytirish (qaytadan sotilgani uchun)
        product = sale.product
        product.quantity -= sale.quantity
        product.save()

        messages.success(
            request,
            f"Sotuv qayta tiklandi! {sale.quantity} dona {product.name} qaytadan sotildi deb hisoblandi.",
        )

        # Telegram bot orqali xabar yuborish (agar kerak bo'lsa)
        if hasattr(shop, "owner") and hasattr(shop.owner, "telegram_id"):
            # Bu yerda telegram botga xabar yuborish kodi
            pass

        return redirect("sales_history", shop_id=shop.id)

    return render(request, "shop/restore_sale.html", {"sale": sale, "shop": shop})


@login_required
def home_view(request):
    """Asosiy sahifa"""

    # Barcha do‘konlar (egasi yoki xodimi bo‘lgan)
    all_shops = Shop.objects.filter(
        Q(owner=request.user) | Q(staff__user=request.user), is_active=True
    ).distinct()

    # Egasi bo‘lgan do‘konlar
    owned_shops = all_shops.filter(owner=request.user)

    # Xodim bo‘lgan do‘konlar
    staff_shops = all_shops.exclude(owner=request.user)

    # Kutilayotgan arizalar
    pending_applications = ShopApplication.objects.filter(
        user=request.user, status="pending"
    )

    # Rad etilgan arizalar (oxirgi 3 ta)
    rejected_applications = ShopApplication.objects.filter(
        user=request.user, status="rejected"
    ).order_by("-updated_at")[:3]

    context = {
        "shops": all_shops,
        "owned_shops": owned_shops,
        "staff_shops": staff_shops,
        "pending_applications": pending_applications,
        "rejected_applications": rejected_applications,
        "has_shops": all_shops.exists(),
    }

    return render(request, "shop/home.html", context)


@login_required
def shop_application_view(request):
    """Do'kon ochish uchun ariza"""
    if request.method == "POST":
        form = ShopApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()

            # Telegram bot orqali adminga yuborish
            send_application_to_admin(application)

            messages.success(
                request, "Arizangiz muvaffaqiyatli yuborildi! Admin ko'rib chiqadi."
            )
            return redirect("home")
    else:
        form = ShopApplicationForm()

    categories = ShopCategory.objects.all()

    return render(
        request, "shop/application.html", {"form": form, "categories": categories}
    )


@login_required
def shop_detail_view(request, shop_id):
    """Do'kon tafsilotlari"""
    shop = get_object_or_404(Shop, id=shop_id, is_active=True)

    # Foydalanuvchi huquqlarini tekshirish
    is_owner = shop.owner == request.user
    staff_position = ShopStaff.objects.filter(shop=shop, user=request.user).first()

    if not is_owner and not staff_position:
        messages.error(request, "Sizda bu do'konni ko'rish huquqi yo'q!")
        return redirect("home")

    # Mahsulotlar
    products = Product.objects.filter(shop=shop)

    # To'liq statistika
    total_products_count = products.count()
    total_products_quantity = products.aggregate(total=Sum("quantity"))["total"] or 0

    # Jami sotuv
    total_sales = shop.get_total_sales_amount()
    total_sales_quantity = shop.get_total_sales_quantity()

    # Bekor qilingan
    total_cancelled = shop.get_total_cancelled_amount()
    cancelled_quantity = (
        shop.sales.filter(is_cancelled=True).aggregate(total=Sum("quantity"))["total"]
        or 0
    )

    # Qolgan mahsulotlarning qiymati
    remaining_value = shop.get_remaining_value()

    # Foydalar
    net_sales = total_sales - total_cancelled

    context = {
        "shop": shop,
        "products": products,
        "is_owner": is_owner,
        "staff_position": staff_position,
        "total_products_count": total_products_count,
        "total_products_quantity": total_products_quantity,
        "total_sales": total_sales,
        "total_sales_quantity": total_sales_quantity,
        "total_cancelled": total_cancelled,
        "cancelled_quantity": cancelled_quantity,
        "remaining_value": remaining_value,
        "net_sales": net_sales,
    }

    return render(request, "shop/shop_detail.html", context)


@login_required
def shop_settings_view(request, shop_id):
    """Do'kon sozlamalari"""
    shop = get_object_or_404(Shop, id=shop_id, owner=request.user)

    if request.method == "POST":
        form = ShopForm(request.POST, request.FILES, instance=shop)
        if form.is_valid():
            form.save()
            messages.success(request, "Do'kon ma'lumotlari yangilandi!")
            return redirect("shop_detail", shop_id=shop.id)
    else:
        form = ShopForm(instance=shop)

    # Qo'shimcha statistika
    total_products = shop.get_total_products()
    total_sales = shop.get_total_sales_amount()
    total_cancelled = shop.get_total_cancelled_amount()
    remaining_value = shop.get_remaining_value()

    context = {
        "shop": shop,
        "form": form,
        "total_products": total_products,
        "total_sales": total_sales,
        "total_cancelled": total_cancelled,
        "remaining_value": remaining_value,
    }

    return render(request, "shop/shop_settings.html", context)


@login_required
def add_staff_view(request, shop_id):
    """Xodim qo'shish"""
    shop = get_object_or_404(Shop, id=shop_id, owner=request.user)

    if request.method == "POST":
        form = StaffForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            role = form.cleaned_data["role"]

            # Yangi user yaratish yoki mavjudini topish
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.save()
                messages.info(request, f"Yangi foydalanuvchi {username} yaratildi.")

            # Xodimni qo'shish
            staff, staff_created = ShopStaff.objects.get_or_create(
                shop=shop, user=user, defaults={"role": role, "added_by": request.user}
            )

            if staff_created:
                messages.success(
                    request,
                    f"{username} muvaffaqiyatli {staff.get_role_display()} sifatida qo'shildi!",
                )
            else:
                messages.warning(request, "Bu foydalanuvchi allaqachon xodim!")

            return redirect("shop_detail", shop_id=shop.id)
    else:
        form = StaffForm()

    staff_list = ShopStaff.objects.filter(shop=shop).select_related("user", "added_by")

    return render(
        request,
        "shop/add_staff.html",
        {"shop": shop, "form": form, "staff_list": staff_list},
    )


@login_required
def add_product_view(request, shop_id):
    """Mahsulot qo'shish"""
    shop = get_object_or_404(Shop, id=shop_id)

    # Foydalanuvchi owner yoki admin ekanligini tekshirish
    is_owner = shop.owner == request.user
    staff_position = ShopStaff.objects.filter(
        shop=shop, user=request.user, role="admin"
    ).first()

    if not is_owner and not staff_position:
        messages.error(request, "Sizda mahsulot qo'shish huquqi yo'q!")
        return redirect("shop_detail", shop_id=shop.id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # Narxni tozalash (bo'shliqlarni olib tashlash)
            price = form.cleaned_data.get("price", "0")

            if isinstance(price, str):
                # Bo'shliq va vergullarni olib tashlash
                price = price.replace(" ", "").replace(",", "")
                try:
                    price = Decimal(price)
                except:
                    messages.error(request, "Narx noto'g'ri formatda!")
                    return render(
                        request, "shop/add_product.html", {"shop": shop, "form": form}
                    )

            # Miqdorni tozalash
            quantity = form.cleaned_data.get("quantity", "0")
            if isinstance(quantity, str):
                quantity = quantity.replace(" ", "").replace(",", "")
                try:
                    quantity = int(quantity)
                except:
                    quantity = 0

            product = form.save(commit=False)
            product.shop = shop
            product.added_by = request.user
            product.price = price  # Tozalangan narx
            product.quantity = quantity  # Tozalangan miqdor
            product.save()

            # Kirim tarixini saqlash
            ProductIncome.objects.create(
                product=product, quantity=product.quantity, added_by=request.user
            )

            messages.success(
                request, f"Mahsulot '{product.name}' muvaffaqiyatli qo'shildi!"
            )
            return redirect("shop_detail", shop_id=shop.id)
        else:
            # Forma noto'g'ri bo'lsa
            messages.error(request, "Formani to'ldirishda xatolik!")
    else:
        form = ProductForm()

    return render(request, "shop/add_product.html", {"shop": shop, "form": form})


@login_required
def product_detail_view(request, product_id):
    """Mahsulot tafsilotlari"""
    product = get_object_or_404(Product, id=product_id)
    shop = product.shop

    # Huquqlarni tekshirish
    is_owner = shop.owner == request.user
    staff_position = ShopStaff.objects.filter(shop=shop, user=request.user).first()

    if not is_owner and not staff_position:
        messages.error(request, "Sizda bu mahsulotni ko'rish huquqi yo'q!")
        return redirect("home")

    # To'liq statistika
    total_income = product.get_total_income()
    total_sold = product.get_total_sold()
    remaining = product.get_remaining()
    total_revenue = product.get_total_revenue()
    total_value = product.get_total_value()

    # Tarix
    income_history = ProductIncome.objects.filter(product=product).select_related(
        "added_by"
    )[:10]
    sales_history = Sale.objects.filter(product=product).select_related(
        "cashier", "cancelled_by"
    )[:10]

    context = {
        "product": product,
        "shop": shop,
        "is_owner": is_owner,
        "staff_position": staff_position,
        "total_income": total_income,
        "total_sold": total_sold,
        "remaining": remaining,
        "total_revenue": total_revenue,
        "total_value": total_value,
        "income_history": income_history,
        "sales_history": sales_history,
    }

    return render(request, "shop/product_detail.html", context)


@login_required
def edit_product_view(request, product_id):
    """Mahsulotni tahrirlash"""
    product = get_object_or_404(Product, id=product_id)
    shop = product.shop

    # Huquqlarni tekshirish
    is_owner = shop.owner == request.user
    is_admin = ShopStaff.objects.filter(
        shop=shop, user=request.user, role="admin"
    ).exists()

    if not is_owner and not is_admin:
        messages.error(request, "Sizda bu mahsulotni tahrirlash huquqi yo'q!")
        return redirect("product_detail", product_id=product.id)

    if request.method == "POST":
        old_quantity = product.quantity
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            product = form.save()

            # Agar miqdor o'zgargan bo'lsa, kirim tarixiga qo'shish
            new_quantity = form.cleaned_data["quantity"]
            if new_quantity > old_quantity:
                ProductIncome.objects.create(
                    product=product,
                    quantity=new_quantity - old_quantity,
                    added_by=request.user,
                )
                messages.success(
                    request,
                    f"Mahsulot yangilandi! +{new_quantity - old_quantity} dona qo'shildi.",
                )
            else:
                messages.success(request, "Mahsulot ma'lumotlari yangilandi!")

            return redirect("product_detail", product_id=product.id)
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "shop/edit_product.html",
        {"product": product, "shop": shop, "form": form},
    )


@login_required
def delete_product_view(request, product_id):
    """Mahsulotni o'chirish"""
    product = get_object_or_404(Product, id=product_id)
    shop = product.shop

    # Faqat owner o'chira oladi
    if shop.owner != request.user:
        messages.error(request, "Faqat do'kon egasi mahsulotni o'chira oladi!")
        return redirect("product_detail", product_id=product.id)

    if request.method == "POST":
        shop_id = product.shop.id
        product_name = product.name
        product.delete()
        messages.success(request, f"Mahsulot '{product_name}' o'chirildi!")
        return redirect("shop_detail", shop_id=shop_id)

    return render(
        request, "shop/delete_product.html", {"product": product, "shop": shop}
    )


@login_required
def sell_product_view(request, shop_id):
    """Mahsulot sotish"""
    shop = get_object_or_404(Shop, id=shop_id)

    # Huquqlarni tekshirish (owner, admin, cashier)
    is_owner = shop.owner == request.user
    staff_position = ShopStaff.objects.filter(shop=shop, user=request.user).first()

    if not is_owner and not staff_position:
        messages.error(request, "Sizda sotuv qilish huquqi yo'q!")
        return redirect("shop_detail", shop_id=shop.id)

    products = Product.objects.filter(shop=shop, quantity__gt=0)

    if request.method == "POST":
        form = SaleForm(request.POST, shop=shop)
        if form.is_valid():
            product = form.cleaned_data["product"]
            quantity = form.cleaned_data["quantity"]

            if product.quantity < quantity:
                messages.error(
                    request,
                    f"Omborda yetarli mahsulot yo'q! Mavjud: {product.quantity} dona",
                )
            else:
                # Sotuvni saqlash
                sale = form.save(commit=False)
                sale.shop = shop
                sale.unit_price = product.price
                sale.total_amount = Decimal(str(quantity)) * product.price
                sale.cashier = request.user
                sale.save()

                # Mahsulot miqdorini kamaytirish
                product.quantity -= quantity
                product.save()

                messages.success(
                    request,
                    f"Sotuv muvaffaqiyatli! {quantity} dona {product.name} sotildi. "
                    f"Summa: {sale.total_amount:,.0f} so'm",
                )
                return redirect("shop_detail", shop_id=shop.id)
    else:
        form = SaleForm(shop=shop)

    return render(
        request,
        "shop/sell_product.html",
        {"shop": shop, "form": form, "products": products},
    )


@login_required
def sales_history_view(request, shop_id):
    """Sotuvlar tarixi"""
    shop = get_object_or_404(Shop, id=shop_id)

    # Huquqlarni tekshirish
    is_owner = shop.owner == request.user
    staff_position = ShopStaff.objects.filter(shop=shop, user=request.user).first()

    if not is_owner and not staff_position:
        messages.error(request, "Sizda sotuvlarni ko'rish huquqi yo'q!")
        return redirect("home")

    sales = (
        Sale.objects.filter(shop=shop)
        .select_related("product", "cashier", "cancelled_by")
        .order_by("-created_at")
    )

    # To'liq statistika
    total_sales = sales.filter(is_cancelled=False).aggregate(total=Sum("total_amount"))[
        "total"
    ] or Decimal("0.00")

    total_sales_quantity = (
        sales.filter(is_cancelled=False).aggregate(total=Sum("quantity"))["total"] or 0
    )

    total_cancelled = sales.filter(is_cancelled=True).aggregate(
        total=Sum("total_amount")
    )["total"] or Decimal("0.00")

    cancelled_quantity = (
        sales.filter(is_cancelled=True).aggregate(total=Sum("quantity"))["total"] or 0
    )

    net_sales = total_sales - total_cancelled

    context = {
        "shop": shop,
        "sales": sales,
        "total_sales": total_sales,
        "total_sales_quantity": total_sales_quantity,
        "total_cancelled": total_cancelled,
        "cancelled_quantity": cancelled_quantity,
        "net_sales": net_sales,
        "is_owner": is_owner,
        "staff_position": staff_position,
    }

    return render(request, "shop/sales_history.html", context)


@login_required
def cancel_sale_view(request, sale_id):
    """Sotuvni bekor qilish"""
    sale = get_object_or_404(Sale, id=sale_id)
    shop = sale.shop

    # Huquqlarni tekshirish
    is_owner = shop.owner == request.user
    is_cashier = ShopStaff.objects.filter(
        shop=shop, user=request.user, role="cashier"
    ).exists()
    is_admin = ShopStaff.objects.filter(
        shop=shop, user=request.user, role="admin"
    ).exists()

    if not is_owner and not is_cashier and not is_admin:
        messages.error(request, "Sizda sotuvni bekor qilish huquqi yo'q!")
        return redirect("sales_history", shop_id=shop.id)

    if sale.is_cancelled:
        messages.warning(request, "Bu sotuv allaqachon bekor qilingan!")
        return redirect("sales_history", shop_id=shop.id)

    if request.method == "POST":
        # Sotuvni bekor qilish
        sale.is_cancelled = True
        sale.cancelled_by = request.user
        from django.utils import timezone

        sale.cancelled_at = timezone.now()
        sale.save()

        # Mahsulot miqdorini qaytarish
        product = sale.product
        product.quantity += sale.quantity
        product.save()

        messages.success(
            request,
            f"Sotuv bekor qilindi! {sale.quantity} dona {product.name} omborda qaytarildi.",
        )
        return redirect("sales_history", shop_id=shop.id)

    return render(request, "shop/cancel_sale.html", {"sale": sale, "shop": shop})


logger = logging.getLogger(__name__)


@csrf_exempt
def telegram_webhook(request):
    """Telegram webhook"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            logger.info(f"Webhook data: {data}")

            # Bu yerda webhook ma'lumotlarini qayta ishlash
            # Aslida bot polling orqali ishlaydi, lekin webhook ham qo'shish mumkin

            return JsonResponse({"status": "ok"})
        except Exception as e:
            logger.error(f"Webhook xatolik: {e}")
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "method not allowed"}, status=405)


@login_required
def bot_status(request):
    """Bot holati"""
    from django.conf import settings

    status = {
        "bot_username": "ShopControlBot",
        "is_active": True,
        "admin_chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
        "total_users": 0,  # Bu yerda haqiqiy ma'lumotlar
        "pending_applications": 0,
    }

    return JsonResponse(status)


@login_required
def telegram_users(request):
    """Telegram foydalanuvchilari"""
    from shop.models import TelegramUser

    users = TelegramUser.objects.all().select_related("user")
    user_list = []

    for user in users:
        user_list.append(
            {
                "id": user.id,
                "username": user.user.username,
                "telegram_id": user.telegram_id,
                "telegram_username": user.username,
                "phone": user.phone,
                "is_active": user.is_bot_active,
                "created_at": user.created_at.strftime("%d.%m.%Y %H:%M"),
            }
        )

    return JsonResponse({"users": user_list})
