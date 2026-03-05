from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from config.decorators import admin_required

from .models import (
    Allergen,
    Product,
    ProductCategory,
)

from .forms import CreateAllergenForm


def inventory_home(request):
    return render(request, "inventory.html")


@admin_required
@transaction.atomic
def allergen_create(request):
    if request.method == "POST":
        form = CreateAllergenForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            if Allergen.objects.filter(name=cd["name"]).exists():
                form.add_error("name", "This allergen already exists.")
                return render(
                    request,
                    "allergens/create_allergen.html",
                    {"form": form, "action": "Create"},
                )

            Allergen.objects.create(name=cd["name"])

            messages.success(request, "Allergen created successfully.")
            return redirect("inventory:inventory_home")
    else:
        form = CreateAllergenForm()

    return render(request, "allergens/create_allergen.html", {"form": form, "action": "Create"})


# ==========================================================
# MARKETPLACE (Customer) - DB CONNECTED
# Templates are in: applications/inventory_management/templates/Dashboards/
# ==========================================================

def _categories_qs():
    return ProductCategory.objects.order_by("name")


def _marketplace_qs():
    """
    Only show products whose availability is marked as available in DB.
    """
    return (
        Product.objects
        .select_related("business", "category", "unit", "availability", "stock")
        .prefetch_related("productallergen_set__allergen")
        .filter(availability__is_available=True)
        .order_by("-id")
    )


def market_home(request):
    categories = list(_categories_qs())
    products = list(_marketplace_qs()[:60])

    return render(
        request,
        "Dashboards/home.html",
        {"products": products, "categories": categories, "q": ""},
    )


def market_category(request, category):
    categories = list(_categories_qs())

    # URL: vegetables -> DB: "Vegetables" (case-insensitive)
    cat_obj = get_object_or_404(ProductCategory, name__iexact=category.replace("-", " "))
    products = list(_marketplace_qs().filter(category=cat_obj))

    return render(
        request,
        "Dashboards/category.html",
        {"category": cat_obj.name, "products": products, "categories": categories, "q": ""},
    )


def market_search(request):
    categories = list(_categories_qs())
    q = (request.GET.get("q") or "").strip()

    products = []
    if q:
        products = list(_marketplace_qs().filter(name__icontains=q))

    return render(
        request,
        "Dashboards/search.html",
        {"q": q, "products": products, "categories": categories},
    )


def market_product_detail(request, pid):
    categories = list(_categories_qs())
    p = get_object_or_404(_marketplace_qs(), pk=pid)

    allergens = [pa.allergen.name for pa in p.productallergen_set.all() if pa.allergen_id]

    return render(
        request,
        "Dashboards/product_detail.html",
        {"p": p, "allergens": allergens, "categories": categories, "q": ""},
    )