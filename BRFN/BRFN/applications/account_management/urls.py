from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.accounts_home, name="accounts_home"),

    # Test Model Joins
    path("users/", views.user_list, name="user_list"),

    # Registration (TC-001, TC-002)
    path("register/customer/", views.customer_register, name="customer_register"),
    path("register/producer/", views.producer_register, name="producer_register"),
    path("register/admin/", views.admin_register, name="admin_register"),


    # Auth (TC-022) 
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]