from django.urls import path, include

urlpatterns = [
    path("accounts/", include("BRFN.Applications.AccountManagment.urls")),
]