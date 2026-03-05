from django.urls import path
from . import views

app_name = "marketplace"

urlpatterns = [
    path("", views.market_home, name="home"),
    path("search/", views.market_search, name="search"),
    path("category/<str:category>/", views.market_category, name="category"),
    path("product/<int:pid>/", views.market_product_detail, name="product_detail"),
]