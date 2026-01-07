# shop/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from decimal import Decimal
from .models import (
    ShopCategory,
    ShopApplication,
    Shop,
    ShopStaff,
    Product,
    ProductIncome,
    Sale,
    ProductCategory,
)
from .telegram_utils import send_application_status


@admin.register(ShopCategory)
class ShopCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "total_shops", "created_at"]
    search_fields = ["name"]
    ordering = ["name"]

    def total_shops(self, obj):
        count = Shop.objects.filter(category=obj, is_active=True).count()
        return format_html(
            '<span style="font-weight: bold; color: green;">{}</span>', count
        )

    total_shops.short_description = "Faol Do'konlar"


@admin.register(ShopApplication)
class ShopApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "shop_name",
        "owner_full_name",
        "category",
        "status_badge",
        "created_at",
        "actions_buttons",
    ]
    list_filter = ["status", "category", "created_at"]
    search_fields = ["shop_name", "owner_full_name", "phone_number", "user__username"]
    readonly_fields = ["user", "created_at", "updated_at"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Asosiy Ma'lumotlar",
            {"fields": ("user", "owner_full_name", "shop_name", "category")},
        ),
        ("Aloqa", {"fields": ("phone_number", "description")}),
        ("Holat", {"fields": ("status",)}),
        ("Vaqt", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def status_badge(self, obj):
        colors = {
            "pending": "orange",
            "approved": "green",
            "rejected": "red",
        }
        icons = {
            "pending": "⏳",
            "approved": "✅",
            "rejected": "❌",
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{} {}</span>',
            colors.get(obj.status, "gray"),
            icons.get(obj.status, ""),
            obj.get_status_display(),
        )

    status_badge.short_description = "Holati"

    def actions_buttons(self, obj):
        if obj.status == "pending":
            return format_html(
                '<a class="button" href="{}?action=approve" '
                'style="background-color: green; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; margin-right: 5px;">'
                "✅ Qabul</a> "
                '<a class="button" href="{}?action=reject" '
                'style="background-color: red; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">'
                "❌ Rad</a>",
                reverse("admin:shop_shopapplication_change", args=[obj.id]),
                reverse("admin:shop_shopapplication_change", args=[obj.id]),
            )
        elif obj.status == "approved":
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Qabul qilingan</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">❌ Rad etilgan</span>'
            )

    actions_buttons.short_description = "Amallar"

    def save_model(self, request, obj, form, change):
        old_status = None
        if change:
            old_obj = ShopApplication.objects.get(pk=obj.pk)
            old_status = old_obj.status

        super().save_model(request, obj, form, change)

        # Agar status o'zgargan bo'lsa
        if change and old_status != obj.status:
            if obj.status == "approved":
                # Do'kon yaratish
                shop, created = Shop.objects.get_or_create(
                    owner=obj.user,
                    name=obj.shop_name,
                    defaults={
                        "category": obj.category,
                        "phone": obj.phone_number,
                        "description": obj.description,
                    },
                )
                if created:
                    self.message_user(
                        request, f"✅ Do'kon muvaffaqiyatli yaratildi: {shop.name}"
                    )
                else:
                    self.message_user(
                        request, f"⚠️ Bu do'kon allaqachon mavjud: {shop.name}"
                    )

            # Telegram orqali xabar yuborish
            send_application_status(obj, obj.status)

    def response_change(self, request, obj):
        if "action" in request.GET:
            action = request.GET.get("action")

            if action == "approve" and obj.status == "pending":
                obj.status = "approved"
                obj.save()
                # Do'kon yaratish
                shop, created = Shop.objects.create(
                    owner=obj.user,
                    name=obj.shop_name,
                    category=obj.category,
                    phone=obj.phone_number,
                    description=obj.description,
                )
                self.message_user(
                    request, f"✅ Ariza qabul qilindi! Do'kon yaratildi: {shop.name}"
                )
                send_application_status(obj, "approved")

            elif action == "reject" and obj.status == "pending":
                obj.status = "rejected"
                obj.save()
                self.message_user(request, "❌ Ariza rad etildi!")
                send_application_status(obj, "rejected")

        return super().response_change(request, obj)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "owner",
        "category",
        "is_active",
        "is_active_badge",
        "total_products",
        "total_sales_display",
        "created_at",
    ]
    list_filter = ["is_active", "category", "created_at"]
    search_fields = ["name", "owner__username", "phone"]
    readonly_fields = ["created_at", "updated_at", "approved_date", "shop_stats"]
    list_editable = ["is_active"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Asosiy Ma'lumotlar",
            {"fields": ("owner", "name", "category", "image", "description")},
        ),
        ("Aloqa", {"fields": ("phone",)}),
        ("Holat", {"fields": ("is_active", "approved_date")}),
        ("Statistika", {"fields": ("shop_stats",), "classes": ("collapse",)}),
        ("Vaqt", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Faol</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">❌ Faol emas</span>'
        )

    is_active_badge.short_description = "Holat"

    def total_products(self, obj):
        count = obj.get_total_products()
        return format_html('<span style="font-weight: bold;">{}</span>', count)

    total_products.short_description = "Mahsulotlar"

    def total_sales_display(self, obj):
        amount = obj.get_total_sales_amount()
        # Formatlashni alohida qilish
        amount_formatted = "{:,.0f}".format(amount)
        return format_html(
            '<span style="color: green; font-weight: bold;">{} so\'m</span>',
            amount_formatted,
        )

    total_sales_display.short_description = "Jami Sotuv"

    def shop_stats(self, obj):
        # Formatlashlarni alohida qilish
        sales_formatted = "{:,.0f}".format(obj.get_total_sales_amount())
        cancelled_formatted = "{:,.0f}".format(obj.get_total_cancelled_amount())
        remaining_formatted = "{:,.0f}".format(obj.get_remaining_value())

        stats = """
        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 8px;">
            <h3 style="margin-bottom: 15px;">📊 To'liq Statistika</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #e9ecef;">
                    <td style="padding: 8px; font-weight: bold;">Mahsulot turlari:</td>
                    <td style="padding: 8px;">{total_products} ta</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Jami mahsulotlar (dona):</td>
                    <td style="padding: 8px;">{total_quantity} dona</td>
                </tr>
                <tr style="background-color: #e9ecef;">
                    <td style="padding: 8px; font-weight: bold;">Jami sotuv:</td>
                    <td style="padding: 8px; color: green; font-weight: bold;">{sales} so'm</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Sotilgan mahsulotlar:</td>
                    <td style="padding: 8px;">{sales_quantity} dona</td>
                </tr>
                <tr style="background-color: #e9ecef;">
                    <td style="padding: 8px; font-weight: bold;">Bekor qilingan:</td>
                    <td style="padding: 8px; color: red; font-weight: bold;">{cancelled} so'm</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Qolgan mahsulotlar qiymati:</td>
                    <td style="padding: 8px; color: orange; font-weight: bold;">{remaining} so'm</td>
                </tr>
            </table>
        </div>
        """.format(
            total_products=obj.get_total_products(),
            total_quantity=obj.get_total_products_quantity(),
            sales=sales_formatted,
            sales_quantity=obj.get_total_sales_quantity(),
            cancelled=cancelled_formatted,
            remaining=remaining_formatted,
        )
        return format_html(stats)

    shop_stats.short_description = "Do'kon Statistikasi"


@admin.register(ShopStaff)
class ShopStaffAdmin(admin.ModelAdmin):
    list_display = ["id", "shop", "user", "role_badge", "added_by", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["shop__name", "user__username"]
    readonly_fields = ["added_by", "created_at"]

    def role_badge(self, obj):
        colors = {
            "admin": "orange",
            "cashier": "blue",
        }
        icons = {
            "admin": "👨‍💼",
            "cashier": "💰",
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{} {}</span>',
            colors.get(obj.role, "gray"),
            icons.get(obj.role, ""),
            obj.get_role_display(),
        )

    role_badge.short_description = "Lavozim"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "shop",
        "price_formatted",
        "quantity_badge",
        "total_value_display",
        "added_by",
        "created_at",
    ]
    list_filter = ["shop", "created_at"]
    search_fields = ["name", "shop__name"]
    readonly_fields = ["added_by", "created_at", "updated_at", "product_stats"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Asosiy Ma'lumotlar", {"fields": ("shop", "name", "image")}),
        ("Narx va Miqdor", {"fields": ("price", "quantity")}),
        ("Statistika", {"fields": ("product_stats",), "classes": ("collapse",)}),
        (
            "Qo'shimcha",
            {
                "fields": ("added_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def price_formatted(self, obj):
        # format specifier ni alohida ishlatish
        formatted_price = "{:,.0f}".format(obj.price)
        return format_html(
            '<span style="font-weight: bold;">{} so\'m</span>', formatted_price
        )

    price_formatted.short_description = "Narxi"

    def quantity_badge(self, obj):
        if obj.quantity > 10:
            color = "green"
            icon = "✅"
        elif obj.quantity > 0:
            color = "orange"
            icon = "⚠️"
        else:
            color = "red"
            icon = "❌"

        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{} {} dona</span>',
            color,
            icon,
            obj.quantity,
        )

    quantity_badge.short_description = "Qoldiq"

    def total_value_display(self, obj):
        value = obj.get_total_value()
        formatted_value = "{:,.0f}".format(value)
        return format_html(
            '<span style="color: orange; font-weight: bold;">{} so\'m</span>',
            formatted_value,
        )

    total_value_display.short_description = "Qiymat"

    def product_stats(self, obj):
        # Formatlashlarni alohida qilish
        revenue_formatted = "{:,.0f}".format(obj.get_total_revenue())
        value_formatted = "{:,.0f}".format(obj.get_total_value())

        stats = """
        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 8px;">
            <h3 style="margin-bottom: 15px;">📊 Mahsulot Statistikasi</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #e9ecef;">
                    <td style="padding: 8px; font-weight: bold;">Jami kirim:</td>
                    <td style="padding: 8px;">{total_income} dona</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Jami sotilgan:</td>
                    <td style="padding: 8px; color: red;">{total_sold} dona</td>
                </tr>
                <tr style="background-color: #e9ecef;">
                    <td style="padding: 8px; font-weight: bold;">Qolgan:</td>
                    <td style="padding: 8px; color: green; font-weight: bold;">{remaining} dona</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Jami tushum:</td>
                    <td style="padding: 8px; color: green; font-weight: bold;">{revenue} so'm</td>
                </tr>
                <tr style="background-color: #e9ecef;">
                    <td style="padding: 8px; font-weight: bold;">Qolgan qiymat:</td>
                    <td style="padding: 8px; color: orange; font-weight: bold;">{value} so'm</td>
                </tr>
            </table>
        </div>
        """.format(
            total_income=obj.get_total_income(),
            total_sold=obj.get_total_sold(),
            remaining=obj.get_remaining(),
            revenue=revenue_formatted,
            value=value_formatted,
        )
        return format_html(stats)

    product_stats.short_description = "Mahsulot Statistikasi"


@admin.register(ProductIncome)
class ProductIncomeAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "quantity", "added_by", "created_at"]
    list_filter = ["created_at", "product__shop"]
    search_fields = ["product__name"]
    readonly_fields = ["added_by", "created_at"]
    date_hierarchy = "created_at"


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "product",
        "shop",
        "quantity",
        "total_amount_formatted",
        "customer_name",
        "cashier",
        "status_badge",
        "cancelled_info",
        "restored_info",
        "created_at",
    ]
    list_filter = ["is_cancelled", "shop", "created_at"]
    search_fields = ["product__name", "customer_name", "cashier__username"]
    readonly_fields = [
        "cashier",
        "is_cancelled",
        "cancelled_by",
        "cancelled_at",
        "restored_by",
        "restored_at",
        "restoration_reason",
        "created_at",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Sotuv Ma'lumotlari",
            {"fields": ("shop", "product", "quantity", "unit_price", "total_amount")},
        ),
        ("Mijoz", {"fields": ("customer_name", "cashier")}),
        (
            "Bekor qilish",
            {
                "fields": ("is_cancelled", "cancelled_by", "cancelled_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Qayta tiklash",  # Yangi section
            {
                "fields": ("restored_by", "restored_at", "restoration_reason"),
                "classes": ("collapse",),
            },
        ),
        ("Vaqt", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def total_amount_formatted(self, obj):
        formatted_amount = "{:,.0f}".format(obj.total_amount)
        return format_html(
            '<span style="font-weight: bold; color: green;">{} so\'m</span>',
            formatted_amount,
        )

    total_amount_formatted.short_description = "Jami Summa"

    def status_badge(self, obj):
        if obj.is_cancelled:
            return format_html(
                '<span style="background-color: red; color: white; padding: 5px 10px; border-radius: 5px;">❌ Bekor qilingan</span>'
            )
        return format_html(
            '<span style="background-color: green; color: white; padding: 5px 10px; border-radius: 5px;">✅ Sotilgan</span>'
        )

    status_badge.short_description = "Holat"

    def restored_info(self, obj):
        if obj.restored_at:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 4px;">'
                '<i class="fas fa-redo"></i> {}'
                "</span><br><small>{}</small>",
                obj.restored_at.strftime("%d.%m.%Y %H:%M"),
                obj.restored_by.username if obj.restored_by else "Noma'lum",
            )
        return "-"

    restored_info.short_description = "Qayta tiklandi"

    def cancelled_info(self, obj):
        if obj.is_cancelled and obj.cancelled_at:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 4px;">'
                '<i class="fas fa-times"></i> {}'
                "</span><br><small>{}</small>",
                obj.cancelled_at.strftime("%d.%m.%Y %H:%M"),
                obj.cancelled_by.username if obj.cancelled_by else "Noma'lum",
            )
        return "-"

    cancelled_info.short_description = "Bekor qilindi"


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "product_count", "created_at"]
    search_fields = ["name"]
    ordering = ["name"]
    list_per_page = 20

    def product_count(self, obj):
        count = Product.objects.filter(category=obj).count()
        return format_html(
            '<span style="font-weight: bold; color: #667eea;">{}</span>', count
        )

    product_count.short_description = "Mahsulotlar soni"


# Admin panel sozlamalari
admin.site.site_header = "🏪 ShopControl Boshqaruv Paneli"
admin.site.site_title = "ShopControl Admin"
admin.site.index_title = "Asosiy Boshqaruv Paneli"
