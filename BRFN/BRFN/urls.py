from django.urls import path, include

urlpatterns = [
    path("accounts/", include("Applications.AccountManagment.urls")),
]