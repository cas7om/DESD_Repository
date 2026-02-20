from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.accounts_home, name="home"),
    path("user/list/", views.user_list, name="user_list"),
    path("user/create/", views.user_create, name="user_create"), 
]