# shop/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import ShopApplication, Shop, Product, ShopStaff, Sale


class RegisterForm(forms.ModelForm):
    """Ro'yxatdan o'tish formasi"""

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Parol"}
        ),
        label="Parol",
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Parolni tasdiqlang"}
        ),
        label="Parolni tasdiqlang",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Login"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ism"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Familiya"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
        }
        labels = {
            "username": "Login",
            "first_name": "Ism",
            "last_name": "Familiya",
            "email": "Email",
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Parollar mos kelmaydi!")

        return cleaned_data


class LoginForm(forms.Form):
    """Tizimga kirish formasi"""

    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Login"}),
        label="Login",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Parol"}
        ),
        label="Parol",
    )


class ShopApplicationForm(forms.ModelForm):
    """Do'kon arizasi formasi"""

    class Meta:
        model = ShopApplication
        fields = [
            "owner_full_name",
            "shop_name",
            "category",
            "phone_number",
            "description",
        ]
        widgets = {
            "owner_full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ism va familiyangiz"}
            ),
            "shop_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Do'kon nomi"}
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+998 XX XXX XX XX"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Do'koningiz haqida qisqacha ma'lumot",
                    "rows": 4,
                }
            ),
        }
        labels = {
            "owner_full_name": "Ism va familiya",
            "shop_name": "Do'kon nomi",
            "category": "Do'kon turi",
            "phone_number": "Telefon raqami",
            "description": "Do'kon haqida ma'lumot",
        }


class ShopForm(forms.ModelForm):
    """Do'kon tahrirlash formasi"""

    class Meta:
        model = Shop
        fields = ["name", "category", "image", "description", "phone"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Do'kon nomi"}
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+998 XX XXX XX XX"}
            ),
        }
        labels = {
            "name": "Do'kon nomi",
            "category": "Kategoriya",
            "image": "Rasm",
            "description": "Tavsif",
            "phone": "Telefon",
        }


class ProductForm(forms.ModelForm):
    """Mahsulot formasi"""

    class Meta:
        model = Product
        fields = ["name", "category", "image", "price", "quantity", "unit"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Mahsulot nomi"}
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "price": forms.TextInput(  # TextInput ga o'zgartirildi
                attrs={
                    "class": "form-control",
                    "placeholder": "Narxi (so'm)",
                    "data-format": "price",  # Formatlash uchun
                    "id": "id_price",  # ID qo'shildi
                }
            ),
            "quantity": forms.TextInput(  # TextInput ga o'zgartirildi
                attrs={
                    "class": "form-control",
                    "placeholder": "Miqdori",
                    "data-format": "quantity",  # Formatlash uchun
                    "id": "id_quantity",  # ID qo'shildi
                }
            ),
            "unit": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "name": "Mahsulot nomi",
            "category": "Kategoriya",
            "image": "Rasm",
            "price": "Narxi",
            "quantity": "Miqdori",
            "unit": "Miqdor birligi",
        }


class StaffForm(forms.Form):
    """Xodim qo'shish formasi"""

    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Login"}),
        label="Login",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Parol"}
        ),
        label="Parol",
    )
    role = forms.ChoiceField(
        choices=[("admin", "Administrator"), ("cashier", "Kassir")],
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Lavozim",
    )


class SaleForm(forms.ModelForm):
    """Sotuv formasi"""

    class Meta:
        model = Sale
        fields = ["product", "quantity", "customer_name"]
        widgets = {
            "product": forms.Select(
                attrs={"class": "form-control", "id": "id_product"}
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Miqdori",
                    "min": "1",
                    "id": "id_quantity",
                }
            ),
            "customer_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Mijoz ismi (ixtiyoriy)"}
            ),
        }
        labels = {
            "product": "Mahsulot",
            "quantity": "Miqdor",
            "customer_name": "Mijoz ismi",
        }

    def __init__(self, *args, **kwargs):
        shop = kwargs.pop("shop", None)
        super().__init__(*args, **kwargs)
        if shop:
            # Faqat omborda mavjud mahsulotlarni ko'rsatish
            self.fields["product"].queryset = Product.objects.filter(
                shop=shop, quantity__gt=0
            ).select_related("category")

            # Har bir mahsulot uchun miqdor chegarasini o'rnatish
            # Bu JavaScript orqali dinamik ravishda amalga oshiriladi
