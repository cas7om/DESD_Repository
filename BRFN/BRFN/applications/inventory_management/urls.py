from django.urls import path
from . import views
from . import views_producer  # <-- producer view'ları burada olacak

app_name = "inventory"

urlpatterns = [
    # Inventory home
    path("", views.inventory_home, name="inventory_home"),

    # Allergen
    # path("allergen/create/", views.allergen_create, name="create_allergen"),

    # --------------------------
    # Producer Dashboard routes
    # --------------------------
    path("producer/products/", views_producer.producer_products, name="producer_products"),
    path("producer/products/new/", views_producer.producer_product_new, name="producer_product_new"),
    path("producer/products/<int:pk>/edit/", views_producer.producer_product_edit, name="producer_product_edit"),

    path("producer/alerts/", views_producer.producer_alerts, name="producer_alerts"),
    path("producer/orders/", views_producer.producer_orders, name="producer_orders"),
]