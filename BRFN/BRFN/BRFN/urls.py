from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("accounts/", admin.site.urls),
]