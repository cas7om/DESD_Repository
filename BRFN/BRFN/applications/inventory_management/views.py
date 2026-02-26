from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from config.decorators import admin_required

from .models import Allergen

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
                return render(request, "allergens/create_allergen.html", {"form": form, "action": "Create"})

            allergen = Allergen.objects.create(
                name=cd["name"],
            )

            messages.success(request, "Allergen created successfully.")
            return redirect("inventory:inventory_home")
    else:
        form = CreateAllergenForm()

    return render(request, "allergens/create_allergen.html", {"form": form, "action": "Create"})
