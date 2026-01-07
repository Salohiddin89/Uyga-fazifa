# shop/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("", views.home_view, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # Shop Application
    path("application/", views.shop_application_view, name="shop_application"),
    # Shop Management
    path("shop/<int:shop_id>/", views.shop_detail_view, name="shop_detail"),
    path(
        "shop/<int:shop_id>/settings/", views.shop_settings_view, name="shop_settings"
    ),
    path("shop/<int:shop_id>/add-staff/", views.add_staff_view, name="add_staff"),
    # Product Management
    path("shop/<int:shop_id>/add-product/", views.add_product_view, name="add_product"),
    path("product/<int:product_id>/", views.product_detail_view, name="product_detail"),
    path(
        "product/<int:product_id>/edit/", views.edit_product_view, name="edit_product"
    ),
    path(
        "product/<int:product_id>/delete/",
        views.delete_product_view,
        name="delete_product",
    ),
    # Sales
    path("sale/<int:sale_id>/restore/", views.restore_sale_view, name="restore_sale"),
    path("shop/<int:shop_id>/sell/", views.sell_product_view, name="sell_product"),
    path("shop/<int:shop_id>/sales/", views.sales_history_view, name="sales_history"),
    path("sale/<int:sale_id>/cancel/", views.cancel_sale_view, name="cancel_sale"),
    # bot/urls.py (yangi fayl)
    path('webhook/', views.telegram_webhook, name='telegram_webhook'),
    path('status/', views.bot_status, name='bot_status'),
    path('users/', views.telegram_users, name='telegram_users'),

]
