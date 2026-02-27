from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.inventory_home, name="inventory_home"),

    path("allergen/list/", views.allergen_list, name="list_allergen"),
    path("allergen/save/<int:pk>/", views.allergen_save, name="save_allergen"),
]