from django.urls import path
from . import views

urlpatterns = [
    # Marketplace
    path("", views.home, name="home"),
    path("category/<slug:slug>/", views.category, name="category"),
    path("product/<int:pid>/", views.product_detail, name="product_detail"),
    path("search/", views.search, name="search"),

    # Producer dashboard
    path("producer/products/", views.producer_products, name="producer_products"),
    path("producer/products/new/", views.producer_product_new, name="producer_product_new"),
    path("producer/products/<int:pid>/edit/", views.producer_product_edit, name="producer_product_edit"),

    path("producer/orders/", views.producer_orders, name="producer_orders"),
    path("producer/orders/<int:oid>/", views.producer_order_detail, name="producer_order_detail"),
    path("producer/orders/<int:oid>/status/", views.producer_order_status, name="producer_order_status"),

    path("producer/payments/", views.producer_payments, name="producer_payments"),
    path("producer/alerts/", views.producer_alerts, name="producer_alerts"),

    # Admin dashboard (UI)
 path("network-admin/commission/", views.admin_commission, name="admin_commission"),
]