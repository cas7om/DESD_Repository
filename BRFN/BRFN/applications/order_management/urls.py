from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),

    path("checkout/", views.checkout_view, name="checkout"),
    path("confirmation/<str:order_ref>/", views.order_confirmation, name="confirmation"),

    path("history/", views.customer_order_history, name="customer_history"),
    path("history/<str:order_ref>/", views.customer_order_detail, name="customer_order_detail"),
    path("history/<str:order_ref>/reorder/", views.reorder_order, name="reorder_order"),

    path("producer/", views.producer_order_inbox, name="producer_inbox"),
    path("producer/<int:portion_id>/", views.producer_order_detail, name="producer_order_detail"),
    path("producer/<int:portion_id>/status/", views.producer_order_update_status, name="producer_order_update_status"),

    path("settlements/", views.settlements, name="settlements"),
]