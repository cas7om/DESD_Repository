from django.conf.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("accounts/", include("applications.account_management.urls")),
    path("orders/", include("applications.order_management.urls")),
    path("inventory/", include("applications.inventory_management.urls")),
]