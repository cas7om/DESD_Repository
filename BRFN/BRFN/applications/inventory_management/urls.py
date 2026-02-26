from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.inventory_home, name="inventory_home"),

    path("allergen/create/", views.allergen_create, name="create_allergen"),
]