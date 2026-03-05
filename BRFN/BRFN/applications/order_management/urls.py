from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    # TC-006
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),

    # TC-007
    path("checkout/", views.checkout_view, name="checkout"),
    path("confirmation/<str:order_ref>/", views.order_confirmation, name="confirmation"),
]