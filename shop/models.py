# shop/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class ShopCategory(models.Model):
    """Do'kon kategoriyalari"""

    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Do'kon kategoriyasi"
        verbose_name_plural = "Do'kon kategoriyalari"

    def __str__(self):
        return self.name


class ShopApplication(models.Model):
    """Do'kon ochish uchun arizalar"""

    STATUS_CHOICES = [
        ("pending", "Kutilmoqda"),
        ("approved", "Qabul qilindi"),
        ("rejected", "Rad etildi"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shop_applications"
    )
    owner_full_name = models.CharField(
        max_length=200, verbose_name="Egasi ism-familiyasi"
    )
    shop_name = models.CharField(max_length=200, verbose_name="Do'kon nomi")
    category = models.ForeignKey(
        ShopCategory, on_delete=models.SET_NULL, null=True, verbose_name="Do'kon turi"
    )
    phone_number = models.CharField(max_length=20, verbose_name="Telefon raqami")
    description = models.TextField(verbose_name="Do'kon haqida ma'lumot")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Holati"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Do'kon arizasi"
        verbose_name_plural = "Do'kon arizalari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.shop_name} - {self.owner_full_name}"


class Shop(models.Model):
    """Do'konlar"""

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_shops"
    )
    name = models.CharField(max_length=200, verbose_name="Do'kon nomi")
    category = models.ForeignKey(
        ShopCategory, on_delete=models.SET_NULL, null=True, verbose_name="Kategoriya"
    )
    image = models.ImageField(
        upload_to="shops/", blank=True, null=True, verbose_name="Rasm"
    )
    description = models.TextField(blank=True, verbose_name="Tavsif")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    approved_date = models.DateTimeField(
        default=timezone.now, verbose_name="Tasdiqlangan sana"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Do'kon"
        verbose_name_plural = "Do'konlar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_total_products(self):
        """Jami mahsulotlar soni"""
        return self.products.count()

    def get_total_products_quantity(self):
        """Jami mahsulotlar miqdori (dona)"""
        from django.db.models import Sum

        result = self.products.aggregate(total=Sum("quantity"))
        return result["total"] or 0

    def get_total_sales_amount(self):
        """Jami sotuv summasi"""
        from django.db.models import Sum

        result = self.sales.filter(is_cancelled=False).aggregate(
            total=Sum("total_amount")
        )
        return result["total"] or Decimal("0.00")

    def get_total_cancelled_amount(self):
        """Jami bekor qilingan summa"""
        from django.db.models import Sum

        result = self.sales.filter(is_cancelled=True).aggregate(
            total=Sum("total_amount")
        )
        return result["total"] or Decimal("0.00")

    def get_total_sales_quantity(self):
        """Jami sotilgan mahsulotlar miqdori"""
        from django.db.models import Sum

        result = self.sales.filter(is_cancelled=False).aggregate(total=Sum("quantity"))
        return result["total"] or 0

    def get_remaining_value(self):
        """Qolgan mahsulotlarning umumiy qiymati"""
        total = Decimal("0.00")
        for product in self.products.all():
            total += product.price * product.quantity
        return total


class ShopStaff(models.Model):
    """Do'kon xodimlari"""

    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("cashier", "Kassir"),
    ]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="staff")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="staff_positions"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Lavozim")
    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="added_staff"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Do'kon xodimi"
        verbose_name_plural = "Do'kon xodimlari"
        unique_together = ["shop", "user"]

    def __str__(self):
        return f"{self.user.username} - {self.shop.name} ({self.get_role_display()})"


class Product(models.Model):
    """Mahsulotlar"""

    # Miqdor birliklari
    UNIT_CHOICES = [
        ("dona", "dona"),
        ("kg", "kg"),
        ("litr", "litr"),
        ("quti", "quti"),
        ("paket", "paket"),
        ("metr", "metr"),
        ("gramm", "gramm"),
        ("shtuk", "shtuk"),
        ("korobka", "korobka"),
        ("qadoq", "qadoq"),
    ]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200, verbose_name="Nomi")
    category = models.ForeignKey(
        "ProductCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kategoriya",
    )
    image = models.ImageField(
        upload_to="products/", blank=True, null=True, verbose_name="Rasm"
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Narxi")
    quantity = models.IntegerField(default=0, verbose_name="Miqdori")
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default="dona",
        verbose_name="Miqdor birligi",
    )
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.shop.name}"

    def get_display_quantity(self):
        """Formatlangan miqdor ko'rinishi"""
        return f"{self.quantity} {self.unit}"

    def get_total_income(self):
        """Jami kirim"""
        from django.db.models import Sum

        result = self.income_history.aggregate(total=Sum("quantity"))
        return result["total"] or 0

    def get_total_sold(self):
        """Jami sotilgan"""
        from django.db.models import Sum

        result = self.sales.filter(is_cancelled=False).aggregate(total=Sum("quantity"))
        return result["total"] or 0

    def get_remaining(self):
        """Qoldiq"""
        return self.quantity

    def get_total_revenue(self):
        """Jami tushum"""
        from django.db.models import Sum

        result = self.sales.filter(is_cancelled=False).aggregate(
            total=Sum("total_amount")
        )
        return result["total"] or Decimal("0.00")

    def get_total_value(self):
        """Qolgan mahsulotning qiymati"""
        return self.price * self.quantity

    # YANGI: SAVE METHODINI QO'SHING
    def save(self, *args, **kwargs):
        """Saqlashdan oldin narx va miqdorni tozalash"""
        # Narxni tozalash (agar string bo'lsa)
        if isinstance(self.price, str):
            self.price = str(self.price).replace(" ", "").replace(",", "")
            try:
                self.price = Decimal(self.price)
            except:
                pass

        # Miqdorni tozalash (agar string bo'lsa)
        if isinstance(self.quantity, str):
            self.quantity = str(self.quantity).replace(" ", "").replace(",", "")
            try:
                self.quantity = int(self.quantity)
            except:
                self.quantity = 0

        # Miqdor manfiy bo'lmasligi kerak
        if self.quantity < 0:
            self.quantity = 0

        super().save(*args, **kwargs)


class ProductIncome(models.Model):
    """Mahsulot kirimi tarixi"""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="income_history"
    )
    quantity = models.IntegerField(verbose_name="Miqdor")
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mahsulot kirimi"
        verbose_name_plural = "Mahsulot kirimlari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} - {self.quantity} dona"


class Sale(models.Model):
    """Sotuvlar"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="sales")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    quantity = models.IntegerField(verbose_name="Miqdor")
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Birlik narxi"
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Umumiy summa"
    )
    customer_name = models.CharField(
        max_length=200, blank=True, verbose_name="Mijoz ismi"
    )
    cashier = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="sales_made"
    )
    is_cancelled = models.BooleanField(default=False, verbose_name="Bekor qilingan")
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_sales",
    )
    cancelled_at = (models.DateTimeField(null=True, blank=True),)
    created_at = models.DateTimeField(auto_now_add=True)
    restored_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="restored_sales",
        verbose_name="Qayta tiklagan",
    )
    restored_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Qayta tiklandi"
    )
    restoration_reason = models.TextField(
        blank=True, verbose_name="Qayta tiklash sababi"
    )

    class Meta:
        verbose_name = "Sotuv"
        verbose_name_plural = "Sotuvlar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} - {self.quantity} dona"

    def save(self, *args, **kwargs):
        if not self.pk:  # Yangi sotuv
            self.total_amount = Decimal(str(self.quantity)) * self.unit_price
        super().save(*args, **kwargs)

    def restore_sale(self, user, reason=""):
        """Sotuvni qayta tiklash"""
        if not self.is_cancelled:
            raise ValueError("Bu sotuv allaqachon bekor qilinmagan!")

        self.is_cancelled = False
        self.restored_by = user
        self.restoration_reason = reason
        from django.utils import timezone

        self.restored_at = timezone.now()
        self.save()

        # Mahsulot miqdorini kamaytirish
        product = self.product
        product.quantity -= self.quantity
        product.save()

        return self

    def get_status_display_full(self):
        """To'liq holatni ko'rsatish"""
        if self.is_cancelled:
            if self.restored_at:
                return "✅ Qayta tiklandi"
            return "❌ Bekor qilingan"
        return "✅ Sotilgan"

    def get_total_restored_amount(self):
        """Qayta tiklanga sotuvlar summasi"""
        from django.db.models import Sum

        result = self.sales.filter(
            is_cancelled=False, restored_at__isnull=False
        ).aggregate(total=Sum("total_amount"))
        return result["total"] or Decimal("0.00")

    def get_statistics(self):
        """To'liq statistika"""
        return {
            "total_sales": self.get_total_sales_amount(),
            "total_cancelled": self.get_total_cancelled_amount(),
            "total_restored": self.get_total_restored_amount(),
            "net_sales": self.get_total_sales_amount()
            - self.get_total_cancelled_amount()
            + self.get_total_restored_amount(),
            "active_sales": self.sales.filter(
                is_cancelled=False, restored_at__isnull=True
            ).count(),
            "cancelled_sales": self.sales.filter(
                is_cancelled=True, restored_at__isnull=True
            ).count(),
            "restored_sales": self.sales.filter(
                is_cancelled=False, restored_at__isnull=False
            ).count(),
        }


class TelegramUser(models.Model):
    """Telegram foydalanuvchilari"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="telegram")
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    first_name = models.CharField(max_length=100, blank=True, verbose_name="Ism")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Familiya")
    username = models.CharField(
        max_length=100, blank=True, verbose_name="Telegram username"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    is_bot_active = models.BooleanField(default=True, verbose_name="Bot faol")
    language = models.CharField(max_length=10, default="uz", verbose_name="Til")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Telegram foydalanuvchi"
        verbose_name_plural = "Telegram foydalanuvchilar"

    def __str__(self):
        return f"{self.user.username} ({self.telegram_id})"


class BotSession(models.Model):
    """Bot sessiyalari"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bot_sessions"
    )
    session_data = models.JSONField(default=dict, verbose_name="Sessiya ma'lumotlari")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bot sessiyasi"
        verbose_name_plural = "Bot sessiyalari"

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


class ProductCategory(models.Model):
    """Mahsulot kategoriyalari"""

    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mahsulot kategoriyasi"
        verbose_name_plural = "Mahsulot kategoriyalari"
        ordering = ["name"]

    def __str__(self):
        return self.name
