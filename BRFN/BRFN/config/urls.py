from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include("applications.account_management.urls")),
    path("orders/", include("applications.order_management.urls")),
    path("inventory/", include("applications.inventory_management.urls")),

    # Marketplace pages at root: /, /search/, /category/<name>/, /product/<id>/
    path("", include("applications.inventory_management.urls_marketplace")),
]